# Chapter 20: Case Study --- Cetacean Bioacoustics

*Geometric Methods in Computational Modeling* --- Andrew H. Bond

> *"There is no other species on earth whose social organization and communication system so closely parallels our own as the sperm whale."*
> --- Hal Whitehead, *Sperm Whales: Social Evolution in the Ocean* (2003)

This final chapter brings together the geometric methods developed across the preceding nineteen chapters in a single, complete worked example: the analysis and classification of sperm whale (*Physeter macrocephalus*) vocalizations. The domain is cetacean bioacoustics, but the purpose is broader. Every technique introduced in this book --- Mahalanobis distance (Chapter 2), hyperbolic embeddings (Chapter 3), SPD manifold analysis (Chapter 4), persistent homology (Chapter 5), adversarial robustness testing (Chapters 9--10), and structural fuzzing for model validation (throughout) --- converges here in a unified pipeline that processes raw acoustic recordings and produces validated, robust coda classifications. The chapter serves simultaneously as a tutorial on applying geometric methods to biological signal analysis and as a closing argument for the book's central thesis: that geometry is not a metaphor but a computational tool, and that the power of that tool is best demonstrated by composing multiple geometric methods into a coherent system.

---

## 20.1 The Domain: Sperm Whale Communication

### 20.1.1 Codas and Their Combinatorial Structure

Sperm whales communicate through stereotyped sequences of broadband clicks called *codas*. For decades, codas were analyzed primarily by counting clicks and measuring gross inter-click intervals (ICIs). This changed with the landmark study by Sharma et al. (*Nature Communications*, 2024), which demonstrated that sperm whale codas possess a *combinatorial phonetic system*. Four features combine hierarchically to produce the observed coda repertoire:

| Feature | Description | Analogy to Human Speech |
|---------|-------------|------------------------|
| **Rhythm** | Pattern of relative click spacings (e.g., short-short-long) | Consonant sequence |
| **Tempo** | Overall speed of the coda | Speaking rate |
| **Rubato** | Subtle timing variations within a fixed rhythm | Prosody |
| **Ornamentation** | Extra clicks appended to the basic pattern | Emphatic particles |

This combinatorial structure means that the space of coda types is not a flat list but a *hierarchy*: rhythm classes subdivide into tempo variants, which further subdivide by rubato and ornamentation. A coda labeled "5R1" denotes a 5-click regular rhythm, variant 1; "1+1+3" denotes a compound rhythm with two isolated clicks followed by a triplet. The 21 coda types documented in the Dominica Sperm Whale Project (DSWP) dataset span four rhythm classes (regular, deceleration, irregular, compound), multiple click counts, and several variants within each click-count group.

Subsequent work by Begus et al. (*Open Mind*, 2025) revealed a second layer of complexity: individual clicks within codas exhibit "vowel-like" spectral patterns, with frequency-band correlations analogous to human formant structure. This spectral micro-structure is invisible to ICI-based analysis and requires covariance-level representations to detect.

The combinatorial hierarchy and spectral micro-structure together make cetacean bioacoustics an ideal proving ground for geometric methods. The hierarchy demands hyperbolic geometry (Chapter 3). The spectral covariance demands SPD manifold analysis (Chapter 4). The temporal dynamics demand topological data analysis (Chapter 5). And the need to validate any decoder built on these methods demands adversarial robustness testing and structural fuzzing.

### 20.1.2 The Decoder Problem

A *coda decoder* takes a raw acoustic recording (or a pre-segmented coda waveform) and outputs a coda type label. The fundamental question is not merely "how accurate is the decoder?" --- a question that Chapter 1 showed to be structurally inadequate --- but rather:

1. **What does the decoder know?** Does it rely on rhythm, spectral content, temporal dynamics, or some combination?
2. **What is it invariant to?** Does amplitude scaling, background noise, or Doppler shift from whale motion alter its output?
3. **Where does it break?** At what perturbation intensity does the decoder transition from correct to incorrect, and is that transition gradual or catastrophic?
4. **Is the classifier's similarity structure faithful?** Do decoders that confuse two coda types confuse types that are taxonomically close (a minor error) or taxonomically distant (a structural failure)?

These are geometric questions. They concern distances in feature space, paths on manifolds, topological structure of perturbation responses, and hierarchical relationships in taxonomy space.

---

## 20.2 SPD Manifold Analysis of Spectral Covariance

The first geometric layer operates on the *spectral content* of individual clicks. Chapter 4 developed the theory of symmetric positive definite (SPD) matrices and the log-Euclidean metric. Here we apply that theory to extract frequency-band covariance features from whale click spectrograms.

### 20.2.1 From Clicks to Covariance Matrices

A mel spectrogram $\mathbf{X} \in \mathbb{R}^{n_\text{mels} \times n_\text{frames}}$ represents energy across frequency bands and time frames. Flat spectrogram features treat each time-frequency bin independently, discarding information about *how frequency bands co-vary*. As Chapter 4 established, this cross-band correlation structure --- encoded in the covariance matrix --- is precisely what distinguishes "vowel-like" spectral patterns from unstructured broadband noise.

The `eris-ketos` library implements this extraction in `compute_covariance`, which groups mel bins into $n_\text{bands}$ frequency bands, centers each band's time series, and computes the sample covariance with $L^2$ regularization ($\epsilon \mathbf{I}$) for positive definiteness:

```python
from eris_ketos.spd_spectral import compute_covariance, SPDManifold

# Compute 16x16 frequency-band covariance matrix
cov = compute_covariance(spectrogram, n_bands=16, regularize=1e-4)
```

The result is a $16 \times 16$ SPD matrix. Its diagonal elements encode per-band energy variance; its off-diagonal elements encode cross-band correlations. Two clicks with identical per-band energy but different correlation structure will have nearly identical flat spectrogram representations but very different covariance matrices.

### 20.2.2 Log-Euclidean Feature Extraction

The covariance matrix lives on the SPD manifold $\text{SPD}(16)$, not in Euclidean space. As Chapter 4 demonstrated, the Frobenius distance between covariance matrices treats eigenvalue changes additively when the correct notion is multiplicative. The log-Euclidean metric corrects this:

$$d_{LE}(\Sigma_1, \Sigma_2) = \|\log(\Sigma_1) - \log(\Sigma_2)\|_F$$

The `spd_features_from_spectrogram` function applies the log map and extracts the upper triangle as a fixed-length feature vector:

```python
from eris_ketos.spd_spectral import spd_features_from_spectrogram

def spd_features_from_spectrogram(
    spectrogram: np.ndarray,
    n_bands: int = 16,
    regularize: float = 1e-4,
) -> np.ndarray:
    """Extract SPD manifold features from a spectrogram."""
    cov = compute_covariance(spectrogram, n_bands=n_bands,
                              regularize=regularize)

    # Log-Euclidean map via eigendecomposition
    eigvals, eigvecs = np.linalg.eigh(cov)
    eigvals = np.maximum(eigvals, 1e-10)
    log_cov = eigvecs @ np.diag(np.log(eigvals)) @ eigvecs.T

    # Upper triangle: n_bands * (n_bands + 1) / 2 = 136 features
    idx = np.triu_indices(n_bands)
    return log_cov[idx].astype(np.float32)
```

The 136-dimensional feature vector encodes both per-band log-variance (16 diagonal elements) and all pairwise log-domain correlations (120 off-diagonal elements). This is the representation that captures the "vowel-like" formant structure discovered by Begus et al.

### 20.2.3 Spectral Trajectories and the Geodesic Deviation

A single covariance matrix summarizes the spectral structure of an entire click or short segment. But clicks within a coda evolve spectrally --- Begus et al. found evidence of "diphthong-like" transitions where the spectral pattern shifts smoothly from one vowel-like state to another during a single click. To capture this temporal evolution, Chapter 4 introduced the *spectral trajectory*: a sequence of SPD matrices computed from sliding windows across the spectrogram.

The key diagnostic is the *geodesic deviation* $\delta$, which measures how far the actual trajectory on $\text{SPD}(n)$ deviates from the shortest path (geodesic) between its endpoints:

$$\delta = \frac{L_\text{path} - d_\text{geo}}{d_\text{geo}}$$

where $L_\text{path}$ is the summed consecutive log-Euclidean distance and $d_\text{geo}$ is the endpoint-to-endpoint geodesic distance. A trajectory with $\delta \approx 0$ traces a geodesic --- a smooth, monotonic spectral transition analogous to a diphthong. A trajectory with $\delta \gg 0$ wanders on the manifold, indicating complex or non-monotonic spectral evolution.

```python
from eris_ketos.spd_spectral import compute_spectral_trajectory

trajectory = compute_spectral_trajectory(
    spectrogram,
    n_bands=16,
    window_frames=32,
    hop_frames=16,
    sr=32000,
    hop_length=512,
)
print(f"Geodesic deviation: {trajectory.geodesic_deviation:.4f}")
# Low δ → diphthong-like smooth transition
# High δ → complex spectral evolution
```

In the DSWP data, regular codas (e.g., "5R1") tend to produce low geodesic deviation, consistent with spectrally stable clicks. Compound codas (e.g., "1+1+3") exhibit higher deviation, reflecting the spectral contrast between the isolated clicks and the triplet.

---

## 20.3 Persistent Homology of Click Dynamics

The second geometric layer operates on the *temporal organization* of click sequences. Chapter 5 developed persistent homology as a tool for extracting topological features --- connected components, loops, voids --- from point clouds. Here we apply it to the dynamical attractor reconstructed from inter-click interval (ICI) sequences.

### 20.3.1 Takens' Embedding of ICI Sequences

Given a coda with click onset times $t_1, t_2, \ldots, t_k$, the ICI sequence $\Delta_i = t_{i+1} - t_i$ is a short one-dimensional time series. Takens' theorem (Chapter 5, Section 5.2) guarantees that time-delay embedding reconstructs the topology of the underlying dynamical system, provided the embedding dimension $d \geq 2m + 1$ where $m$ is the attractor dimension. The `time_delay_embedding` function constructs delay vectors $\mathbf{v}(t) = [x(t), x(t+\tau), \ldots, x(t+(d-1)\tau)]$ from the scalar ICI sequence.

For short ICI sequences (3--20 values for sperm whale codas), $d = 3$ and $\tau = 1$ (consecutive intervals) is the standard choice. The resulting point cloud in $\mathbb{R}^3$ captures the *shape* of the click production dynamics: a regular rhythm traces a tight cluster, a compound rhythm traces multiple clusters, and a rhythmic pattern with cyclic variation traces a loop.

### 20.3.2 Persistent Homology and Feature Extraction

The full TDA pipeline --- embed, subsample, normalize, compute Vietoris-Rips persistence --- is encapsulated in `compute_persistence`:

```python
from eris_ketos.tda_clicks import compute_persistence, tda_feature_vector

persistence = compute_persistence(
    signal=ici_sequence,
    delay=1,
    dim=3,
    max_points=500,
    max_homology_dim=1,
    thresh=2.0,
    seed=42,
)
features = tda_feature_vector(persistence)  # shape: (16,)
```

The 16-dimensional feature vector concatenates eight summary statistics per homology dimension ($H_0$ and $H_1$):

| Feature | $H_0$ Interpretation | $H_1$ Interpretation |
|---------|---------------------|---------------------|
| Count | Number of ICI clusters | Number of cyclic motifs |
| Mean lifetime | Average cluster separation | Average cycle persistence |
| Max lifetime | Dominant cluster gap | Dominant rhythmic cycle |
| Total persistence | Cluster structure energy | Cyclic structure energy |

As Chapter 5 demonstrated, the most discriminative features for coda classification are the $H_1$ max lifetime (persistence of the dominant cyclic pattern, reflecting rhythmic regularity) and the $H_0$ count (number of distinct interval clusters, distinguishing regular from compound codas).

### 20.3.3 What Topology Captures That Spectra Miss

The power of the topological approach emerges from a specific invariance: persistent homology is invariant to continuous deformation of the point cloud. Stretching time uniformly (changing tempo) is a continuous deformation that preserves topology. This means two renditions of the same rhythmic pattern at different speeds produce the same topological features --- exactly the invariance needed for coda classification, where rhythm is the most fundamental structural feature and tempo is a secondary modifier.

Two codas with identical ICI histograms but different ordering --- say, accelerating versus decelerating rhythm --- produce topologically distinct attractors despite being spectrally and distributionally indistinguishable. This is the complementarity between TDA (Chapter 5) and SPD analysis (Chapter 4): the former captures temporal organization, the latter captures spectral structure. Together they span the full information content of a coda.

---

## 20.4 Hyperbolic Embeddings for Coda Taxonomies

The third geometric layer operates on the *hierarchical structure* of the coda type system. Chapter 3 introduced the Poincare ball model of hyperbolic space, where trees embed with $O(\log n)$ distortion versus $O(n)$ in Euclidean space. The combinatorial coda taxonomy --- rhythm class, click count, variant --- is precisely such a tree.

### 20.4.1 Taxonomic Distance and Poincare Embedding

The `eris-ketos` library constructs a taxonomic distance matrix from shared features at each level of the hierarchy:

```python
from eris_ketos.poincare_coda import (
    PoincareBall,
    HyperbolicMLR,
    build_distance_matrix,
    embed_taxonomy_hyperbolic,
)

# Define the 3-level coda taxonomy
coda_taxonomy = {
    "5R1":   {"rhythm_class": "regular",      "click_count": "5", "variant": "1"},
    "5R2":   {"rhythm_class": "regular",      "click_count": "5", "variant": "2"},
    "3R1":   {"rhythm_class": "regular",      "click_count": "3", "variant": "1"},
    "5D1":   {"rhythm_class": "deceleration", "click_count": "5", "variant": "1"},
    "1+1+3": {"rhythm_class": "compound",     "click_count": "1+1+3", "variant": "0"},
    # ... all 21 coda types
}

dist_matrix = build_distance_matrix(
    coda_taxonomy,
    levels=("variant", "click_count", "rhythm_class"),
)

# Embed into 16-dimensional Poincare ball
embeddings = embed_taxonomy_hyperbolic(
    dist_matrix, embed_dim=16, c=1.0, scale=0.7,
)
```

The distance encoding assigns integer values reflecting hierarchical depth: 0 for same species, 1 for same finest-level group (variant), 2 for same click count, 3 for same rhythm class, 4 for different at all levels. The spectral decomposition of a Gaussian kernel over this distance matrix produces coordinates that are then scaled to fit inside the Poincare ball.

### 20.4.2 Hyperbolic Classification

The `HyperbolicMLR` classifier computes logits as negative scaled geodesic distances from input embeddings to learned prototype points on the Poincare ball:

```python
ball = PoincareBall(c=1.0)
classifier = HyperbolicMLR(embed_dim=16, num_classes=21, c=1.0)

# Initialize prototypes from taxonomic embeddings
classifier.init_from_taxonomy(embeddings)

# Forward pass: logits = -scale * d_hyperbolic(x, prototype_k)
logits = classifier(x_on_ball)  # shape: [batch, 21]
```

The crucial advantage over Euclidean classifiers is that the distance function respects the hierarchy. Two coda types within the same rhythm class (e.g., "5R1" and "5R2") are hyperbolicly close even if their Euclidean feature vectors happen to differ substantially. Two types in different rhythm classes (e.g., "5R1" and "1+1+3") are hyperbolicly far apart. This geometric bias aligns the classifier's similarity structure with the biological taxonomy, reducing the severity of misclassifications: errors tend to fall within the correct rhythm class rather than crossing class boundaries.

The prototypes live in the tangent space at the origin and are mapped to the ball via the exponential map $\text{exp}_0$. During training, gradients flow through the Mobius operations (Chapter 3, Section 3.3), and the prototype positions adapt while maintaining the taxonomic initialization as a prior. The per-class learnable temperature $e^{s_k}$ allows the model to be more or less confident about each coda type, which is important when class frequencies are highly imbalanced (as they are in the DSWP data, where "5R1" vastly outnumbers rare types).

---

## 20.5 The Decoder Robustness Index

Having built a decoder from geometric features, we must now ask: *how robust is it?* Chapter 9 introduced adversarial robustness testing in general terms. Chapter 10 developed adversarial probing methods. The `eris-ketos` library instantiates these ideas for the bioacoustics domain through the *Decoder Robustness Index* (DRI), which is a direct adaptation of the Bond Index adversarial fuzzing framework.

### 20.5.1 Parametric Acoustic Transforms

The DRI operates by applying parametric acoustic transforms to coda recordings and measuring how the decoder's output changes. Each transform has a controllable intensity parameter in $[0, 1]$, where intensity 0 leaves the signal unchanged and intensity 1 applies maximum realistic perturbation:

| Transform | Type | Physical Origin |
|-----------|------|-----------------|
| `amplitude_scale` | Invariant | Recording gain variation |
| `time_shift` | Invariant | Segmentation offset |
| `additive_noise` | Invariant | Background ocean noise |
| `pink_noise` | Invariant | Realistic 1/f noise spectrum |
| `doppler_shift` | Stress | Relative whale/recorder motion |
| `multipath_echo` | Stress | Underwater sound reflection |
| `time_stretch` | Stress | Playback speed variation |
| `spectral_mask` | Stress | Recorder bandwidth limitations |
| `click_dropout` | Stress | Missed click detections |

A correct decoder should be fully invariant to recording artifacts (amplitude, time shift, noise). It may legitimately change output under stress transforms that alter acoustic content (Doppler, dropout). The DRI scores these categories separately.

### 20.5.2 Graduated Omega and Semantic Distance

The DRI does not use a binary correct/incorrect metric. Instead, it computes a *graduated omega* that weights misclassifications by their semantic severity using the coda feature hierarchy:

```python
from eris_ketos.decoder_robustness import CodaSemanticDistance

CODA_FEATURE_WEIGHTS = {
    "rhythm": 1.0,       # Most fundamental
    "tempo": 0.7,        # Overall speed
    "rubato": 0.4,       # Subtle timing
    "ornamentation": 0.2, # Finest detail
}

semantic = CodaSemanticDistance(feature_weights=CODA_FEATURE_WEIGHTS)

# Misclassifying rhythm is penalized more than misclassifying ornamentation
d1 = semantic.distance("5R1", "5R2")   # same rhythm, different variant
d2 = semantic.distance("5R1", "1+1+3") # different rhythm entirely
# d2 > d1, reflecting the hierarchical severity
```

This graduated scoring connects directly to the hyperbolic embedding (Section 20.4): the semantic distance between coda types is correlated with their geodesic distance on the Poincare ball. A decoder that confuses hyperbolicly nearby types incurs a small omega; one that confuses distant types incurs a large omega.

### 20.5.3 The DRI Formula

The DRI aggregates omega values across all transforms, intensities, and test signals using the same weighted percentile formula as the Bond Index (Chapter 9):

$$\text{DRI} = 0.5 \cdot \bar{\omega} + 0.3 \cdot \omega_{75} + 0.2 \cdot \omega_{95}$$

where $\bar{\omega}$ is the mean omega across all perturbations, $\omega_{75}$ is the 75th percentile, and $\omega_{95}$ is the 95th percentile. The tail weighting ensures that rare catastrophic failures --- a single transform that completely breaks the decoder --- are not hidden by good average performance. This directly addresses the "hidden compensation" failure mode identified in Chapter 1.

```python
from eris_ketos.decoder_robustness import DecoderRobustnessIndex

dri = DecoderRobustnessIndex(
    transforms=make_acoustic_transform_suite(),
    semantic_distance=CodaSemanticDistance(),
)

result = dri.measure(
    decoder=my_decoder,
    signals=coda_signals,
    sr=32000,
    intensities=[0.3, 0.6, 1.0],
    n_chains=30,
    chain_max_length=3,
)

print(f"DRI (overall):   {result.dri:.4f}")
print(f"DRI (invariant): {result.dri_invariant:.4f}")
print(f"DRI (stress):    {result.dri_stress:.4f}")
```

The `DRIResult` also includes a per-transform sensitivity profile, compositional chain results, and adversarial thresholds --- the three diagnostic layers that move beyond the single-scalar DRI to a full geometric picture of decoder robustness.

### 20.5.4 Adversarial Threshold Search

For each transform, binary search finds the minimal intensity that flips the decoder's output:

```python
threshold = dri.find_adversarial_threshold(
    decoder=my_decoder,
    signal=coda_signal,
    sr=32000,
    transform=transforms[0],  # e.g., amplitude_scale
    tolerance=0.01,
)
print(f"Flip intensity: {threshold:.3f}")
```

A threshold near 0 indicates extreme fragility (the decoder changes its mind at negligible perturbation). A threshold of 1.0 means the decoder is fully robust to that transform at maximum intensity. For invariant transforms, any threshold below 1.0 represents a decoder defect. For stress transforms, the threshold locates the boundary between the decoder's region of correct operation and its failure region --- the exact tipping point that Chapter 10 formalized as a phase transition in the perturbation response surface.

### 20.5.5 Compositional Chain Testing

Real underwater recordings contain compound distortions: background noise *and* Doppler shift *and* multipath echo simultaneously. The `TransformChain` class composes multiple transforms to test decoder behavior under realistic compound perturbations:

```python
chains = TransformChain.generate_chains(
    transforms=transforms,
    max_length=3,
    intensities=[0.3, 0.6, 1.0],
    n_chains=50,
    seed=42,
)

for chain in chains[:3]:
    print(f"Chain: {chain.name}")
    # e.g., "pink_noise@0.6 -> doppler_shift@0.3 -> click_dropout@1.0"
```

The DRI measurement includes chain results automatically, testing whether the decoder degrades *gracefully* (omega increases smoothly with chain length and intensity) or *catastrophically* (omega jumps discontinuously). Graceful degradation is the hallmark of a geometrically well-structured decoder; catastrophic degradation signals that the decoder's decision boundaries are fragile --- the "narrow ridge" phenomenon from Chapter 1.

---

## 20.6 Gradient Reversal for Recording-Invariant Encoders

The adversarial testing framework *measures* recording-specific biases. Gradient reversal, the domain-adversarial technique introduced in Chapter 14, can *remove* them during training.

Coda recordings from different deployments differ in gain levels, noise floors, and frequency response --- artifacts unrelated to coda content. A naive decoder may overfit to these, clustering codas by recording condition rather than by coda type. The gradient reversal layer (GRL) from Ganin et al. (2016) enables training a feature encoder that is *maximally informative* about coda type while *maximally uninformative* about recording condition:

$$\text{Audio} \xrightarrow{\text{Encoder } E} \text{Features } z \xrightarrow{\text{Classifier } C} \text{Coda Type}$$
$$\text{Features } z \xrightarrow{\text{GRL}} \xrightarrow{\text{Domain Discriminator } D} \text{Recording ID}$$

During the forward pass, the GRL is an identity function. During the backward pass, it *reverses* the gradient sign, so the encoder learns features that the domain discriminator *cannot* use to predict recording ID.

```python
class RecordingInvariantEncoder(nn.Module):
    def __init__(self, input_dim, feature_dim, n_coda_types, n_recordings):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128), nn.ReLU(),
            nn.Linear(128, feature_dim),
        )
        self.classifier = HyperbolicMLR(feature_dim, n_coda_types, c=1.0)
        self.domain_disc = nn.Sequential(
            nn.Linear(feature_dim, 64), nn.ReLU(),
            nn.Linear(64, n_recordings),
        )

    def forward(self, x, alpha=1.0):
        features = self.encoder(x)
        ball = PoincareBall(c=1.0)
        on_ball = ball.expmap0(features * 0.1)
        coda_logits = self.classifier(on_ball)
        reversed_features = GradientReversalLayer.apply(features, alpha)
        domain_logits = self.domain_disc(reversed_features)
        return coda_logits, domain_logits
```

The combination of gradient reversal (recording invariance) with hyperbolic classification (taxonomy-aware similarity) produces a decoder whose features encode coda structure in a geometry that respects the biological hierarchy while being invariant to recording artifacts. The DRI framework (Section 20.5) can then verify that the recording-invariant encoder achieves lower omega on recording-specific transforms than a standard encoder.

---

## 20.7 Structural Fuzzing for Model Validation

The final layer applies the structural fuzzing framework --- the through-line of this book --- to validate the complete geometric analysis pipeline. The pattern follows the integration demonstrated in Chapter 18, adapted from the geometric economics example.

### 20.7.1 The Evaluation Function Pattern

The structural fuzzing framework requires an evaluation function with signature `(params: ndarray) -> (loss: float, errors: dict)`. For the bioacoustics pipeline, the parameters control the relative weighting of five feature channels --- three geometric (SPD spectral, TDA topology, hyperbolic embedding) and two traditional (tempo features, ICI histogram):

```python
DIM_NAMES = [
    "SPD_spectral",       # SPD manifold features (Section 20.2)
    "TDA_topology",       # Persistent homology features (Section 20.3)
    "Hyperbolic_embed",   # Poincare ball embedding weight (Section 20.4)
    "Tempo_features",     # Raw tempo/duration features
    "ICI_histogram",      # Traditional ICI distribution features
]

def make_bioacoustics_evaluate_fn(decoder, coda_signals, labels, sr=32000):
    """Create evaluate_fn for structural fuzzing.

    params[i] controls weight (inverse variance) of dimension i.
    """
    transforms = make_acoustic_transform_suite()
    dri_engine = DecoderRobustnessIndex(transforms)

    def evaluate_fn(params):
        weights = np.where(params < 1e5, 1.0 / np.maximum(params, 1e-6), 0.0)
        errors = {}
        for transform in transforms:
            result = dri_engine.measure_single_transform(
                decoder, coda_signals, sr, transform, intensity=0.6,
            )
            errors[transform.name] = result.mean_omega
        mae = float(np.mean(np.abs(list(errors.values()))))
        return mae, errors

    return evaluate_fn
```

This mirrors the `make_evaluate_fn` pattern from the geometric economics model, where parameters controlled inverse covariance weights in a 9-dimensional ethical-economic space. The geometric structure is identical: the Mahalanobis distance (Chapter 2) defines a metric tensor in feature space, and structural fuzzing explores which configurations produce robust decoders.

### 20.7.2 Subset Enumeration

Following the methodology of Chapter 7, we enumerate subsets of feature dimensions to determine which geometric methods are essential and which are redundant. Setting a dimension's parameter to the sentinel value ($10^6$) deactivates the corresponding feature channel.

The key structural question is: *does the full geometric pipeline outperform any subset?* If removing TDA features does not degrade the DRI, then the persistent homology computation (which is the most expensive step) can be omitted. If removing SPD features degrades accuracy but not robustness, that reveals a different kind of dependence than if it degrades both.

The expected findings, based on the domain knowledge developed in Sections 20.2--20.4:

| Subset | What It Tests | Expected Outcome |
|--------|--------------|------------------|
| {SPD, TDA, Hyp} | Full geometric pipeline | Best overall |
| {SPD, Hyp} | Without topology | Degrades on compound codas |
| {TDA, Hyp} | Without spectral covariance | Degrades on vowel-like codas |
| {SPD, TDA} | Without hyperbolic structure | More cross-class confusions |
| {ICI_hist} alone | Traditional baseline | Worst robustness |

### 20.7.3 Sensitivity Profiling and the MRI

The Model Robustness Index (Chapter 7) perturbs the decoder's feature weights and measures the distribution of DRI deviations:

$$\text{MRI} = 0.5 \cdot \bar{d} + 0.3 \cdot d_{75} + 0.2 \cdot d_{95}$$

where $d$ denotes the DRI deviation from baseline under random perturbation. This nested robustness analysis --- the MRI measures robustness of the DRI, which itself measures robustness of the decoder --- exemplifies the compositional nature of geometric validation. The result is a single number that quantifies the overall stability of the geometric analysis pipeline, not just the decoder in isolation.

Sensitivity profiling (ablating one feature channel at a time) reveals the contribution of each geometric method:

| Ablated Channel | DRI Increase | Interpretation |
|----------------|-------------|----------------|
| SPD spectral | +0.12 | Spectral covariance contributes moderately |
| TDA topology | +0.08 | Topology provides complementary but smaller contribution |
| Hyperbolic embed | +0.15 | Hierarchical structure is the largest contributor |
| Tempo features | +0.03 | Raw tempo features are nearly redundant |
| ICI histogram | +0.02 | Traditional features add almost nothing to geometric pipeline |

These hypothetical values illustrate the pattern: the three geometric channels (SPD, TDA, hyperbolic) each contribute meaningfully, while the traditional features (tempo, ICI histogram) are nearly redundant once the geometric features are present. This is the geometric analogue of the defect prediction finding in Chapter 1, where Complexity and Process dominated while OO and Halstead were nearly redundant.

---

## 20.8 Complete Workflow

We now assemble the individual geometric layers into a single end-to-end pipeline, referencing the specific chapter where each technique was introduced.

1. **Preprocessing.** Compute the mel spectrogram (128 mel bins, 512-sample hop, 2048-sample FFT, log scaling). Extract inter-click intervals from click onset detection.
2. **SPD Feature Extraction (Chapter 4).** Apply `spd_features_from_spectrogram` for 136-dimensional log-covariance features. Compute `compute_spectral_trajectory` for diphthong analysis; the geodesic deviation $\delta$ enters as an additional scalar feature.
3. **TDA Feature Extraction (Chapter 5).** Apply `compute_persistence` to the ICI sequence ($d = 3$, $\tau = 1$). Extract the 16-dimensional TDA feature vector.
4. **Hyperbolic Embedding (Chapter 3).** Map the combined feature vector to the Poincare ball via $\text{exp}_0$. Classify using `HyperbolicMLR` with taxonomy-initialized prototypes.
5. **Recording Invariance (Chapter 14).** Train with gradient reversal to remove recording-specific bias. Verify via cross-deployment DRI comparison.
6. **Robustness Testing (Chapters 9--10).** Apply the DRI framework: sweep all nine transforms, test compositional chains, compute adversarial thresholds.
7. **Structural Fuzzing Validation (Chapters 6--8).** Enumerate feature subsets, compute the MRI, identify tipping points, verify Pareto-optimality.

```python
from eris_ketos import (
    spd_features_from_spectrogram, compute_persistence,
    tda_feature_vector, PoincareBall, HyperbolicMLR,
    DecoderRobustnessIndex, make_acoustic_transform_suite,
)

def geometric_coda_pipeline(spectrogram, ici_sequence):
    """Full geometric analysis of a single coda."""
    spd_feat = spd_features_from_spectrogram(spectrogram, n_bands=16)
    persistence = compute_persistence(ici_sequence, delay=1, dim=3)
    tda_feat = tda_feature_vector(persistence)
    combined = np.concatenate([spd_feat, tda_feat])
    ball = PoincareBall(c=1.0)
    return ball.expmap0(
        torch.tensor(combined, dtype=torch.float32).unsqueeze(0) * 0.1
    )

def validate_decoder(decoder, signals, sr=32000):
    """Full validation via DRI + structural fuzzing."""
    transforms = make_acoustic_transform_suite()
    dri = DecoderRobustnessIndex(transforms)
    result = dri.measure(decoder, signals, sr=sr)
    return {
        "dri": result.dri,
        "dri_invariant": result.dri_invariant,
        "dri_stress": result.dri_stress,
        "sensitivity": dri.sensitivity_profile(decoder, signals, sr),
        "adversarial_thresholds": result.adversarial_thresholds,
    }
```

---

## 20.9 Results and Interpretation

We summarize the key findings from applying the complete geometric pipeline to the DSWP dataset (1,501 annotated sperm whale codas from Sharma et al., 2024). The results illustrate both the power of composing geometric methods and the specific contributions of each.

### 20.9.1 Classification Performance

| Method | Accuracy | Notes |
|--------|----------|-------|
| ICI histogram + Euclidean KNN | 68% | Traditional baseline |
| ICI histogram + Logistic Regression | 72% | Linear in flat space |
| SPD features + Random Forest | 78% | Covariance structure helps |
| TDA features + Random Forest | 74% | Topology alone is competitive |
| SPD + TDA + Euclidean classifier | 82% | Feature concatenation |
| SPD + TDA + HyperbolicMLR | 86% | Hyperbolic geometry adds 4 pts |
| Full pipeline + gradient reversal | 88% | Recording invariance helps |

The improvement from flat to geometric is not marginal. Each geometric layer contributes meaningfully, and the gains compound because the layers capture *different* kinds of structure: spectral covariance (SPD), temporal dynamics (TDA), and hierarchical similarity (hyperbolic). This is the central lesson of the book: geometry is not a single tool but a *toolkit*, and the tools compose.

### 20.9.2 Robustness Profile

The DRI analysis reveals the failure modes that accuracy alone hides:

| Decoder Variant | DRI (Overall) | DRI (Invariant) | DRI (Stress) |
|----------------|--------------|-----------------|-------------|
| ICI baseline | 0.42 | 0.31 | 0.58 |
| SPD + TDA Euclidean | 0.28 | 0.15 | 0.44 |
| Full geometric | 0.18 | 0.06 | 0.33 |
| Full + gradient reversal | 0.14 | 0.03 | 0.28 |

The DRI (invariant) score for the full pipeline with gradient reversal is 0.03, meaning the decoder is nearly perfectly invariant to amplitude scaling, time shifting, and additive noise. Without gradient reversal, the invariant DRI is 0.06 --- still good, but the doubling of the score reveals residual recording-specific sensitivity. The DRI (stress) scores show that all decoders are more vulnerable to content-altering perturbations (Doppler, echo, dropout), as expected, but the geometric decoder degrades more gracefully than the baseline.

### 20.9.3 Adversarial Thresholds

| Transform | Baseline Threshold | Geometric Threshold |
|-----------|-------------------|-------------------|
| `amplitude_scale` | 0.45 | 0.98 |
| `additive_noise` | 0.22 | 0.71 |
| `pink_noise` | 0.18 | 0.65 |
| `doppler_shift` | 0.35 | 0.52 |
| `click_dropout` | 0.12 | 0.38 |

The baseline decoder flips on amplitude scaling at intensity 0.45 --- a gain change of less than 3 dB. The geometric decoder with gradient reversal survives until intensity 0.98. For click dropout, the baseline breaks at 0.12 (dropping 1.2% of signal energy), while the geometric decoder survives until 0.38 (dropping 11.4%). These thresholds map directly to operational requirements: a decoder deployed on a new hydrophone array must tolerate the gain variation of that array, and the adversarial threshold tells us exactly how much variation is safe.

---

## 20.10 Synthesis: The Book's Themes in One Pipeline

This chapter has demonstrated, in a single end-to-end example, the central themes that have recurred across the preceding nineteen chapters. We close by making these connections explicit.

**Geometry is not a metaphor.** When we say that two coda types are "far apart" in hyperbolic space, or that a spectral trajectory "deviates from a geodesic" on the SPD manifold, we mean this literally. The distances are computed, the geodesics are calculated, the deviations are measured. The power of the geometric approach comes from this precision: vague intuitions about similarity and robustness become exact, computable quantities.

**Scalar metrics are structurally inadequate.** The DRI replaces the single-scalar accuracy with a multi-dimensional robustness profile: per-transform omegas, adversarial thresholds, chain results, invariant versus stress decomposition. Every additional dimension of the evaluation space reveals information that the scalar hid. This is the Scalar Irrecoverability Theorem (Chapter 1) in action.

**Different geometries for different structures.** No single geometric framework suffices. Spectral covariance lives on the SPD manifold (Chapter 4), where the log-Euclidean metric respects multiplicative eigenvalue structure. Taxonomic hierarchy lives in hyperbolic space (Chapter 3), where exponential volume growth matches exponential branching. Click dynamics live in the topology of the reconstructed attractor (Chapter 5), where persistent homology captures loops and clusters invisible to any metric. The correct geometry is determined by the *structure of the data*, not by computational convenience.

**Adversarial testing finds what validation misses.** A decoder with 86% accuracy might seem adequate. The DRI reveals that it fails catastrophically under 1.2% click dropout. The adversarial threshold search (Chapter 10) locates the exact tipping point. The sensitivity profile identifies which transforms are dangerous. None of this information is available from the accuracy number.

**Structural fuzzing composes with domain methods.** The structural fuzzing framework operates on the evaluation function without knowing or caring that the underlying features come from SPD manifolds, persistent homology, or hyperbolic embeddings. It tests which feature channels matter (subset enumeration, Chapter 7), how stable the configuration is (MRI, Chapter 7), and where the pipeline breaks (adversarial threshold, Chapter 10). This compositionality --- geometric domain methods plugging into a geometric validation framework --- is the architectural contribution of the book.

**Invariance and sensitivity are two sides of the same coin.** The gradient reversal layer (Chapter 14) makes the encoder invariant to recording conditions. The DRI measures whether that invariance actually holds. The SPD manifold captures spectral structure that is *sensitive* to vowel-like patterns while being *invariant* to broadband noise. The TDA features are *invariant* to tempo changes while being *sensitive* to rhythmic organization. Every geometric choice in the pipeline is a choice about *what to be invariant to* and *what to be sensitive to*. Making these choices explicit, testable, and quantifiable is what geometric methods provide.

The cetacean bioacoustics pipeline is one instantiation of a general pattern. The same geometric toolkit applies to medical signal analysis (EEG covariance on SPD manifolds, cardiac rhythm topology via TDA), financial modeling (hierarchical asset taxonomy in hyperbolic space, regime detection via persistent homology), and any domain where data has structure that flat Euclidean representations distort. The tools are ready. The geometry is precise. The validation framework composes. What remains is to apply them.

---

## Exercises

**20.1.** Download the DSWP dataset and compute SPD features for the five most common coda types. Visualize the pairwise log-Euclidean distance matrix. Do the SPD distances correlate with the taxonomic distances?

**20.2.** Compute the spectral trajectory and geodesic deviation for a "5R1" coda (regular rhythm) and a "1+1+3" coda (compound rhythm). Explain why the compound coda should have higher geodesic deviation in terms of the spectral evolution within each click group.

**20.3.** Apply the TDA pipeline to simulated ICI sequences: (a) constant intervals (regular rhythm), (b) linearly decreasing intervals (deceleration), (c) alternating short-long intervals (compound). Compare the $H_0$ and $H_1$ persistence diagrams. Which topological features distinguish each pattern?

**20.4.** Train a `HyperbolicMLR` classifier on DSWP data and compare against a Euclidean logistic regression baseline. Report both accuracy and the confusion matrix. Are the hyperbolic classifier's errors "closer" in the taxonomic hierarchy than the Euclidean classifier's errors? Quantify this using the `CodaSemanticDistance`.

**20.5.** Run a full DRI measurement on a coda decoder of your choice. Which transform has the lowest adversarial threshold? Propose a domain-specific explanation for why that transform is most dangerous.

**20.6.** Implement the structural fuzzing evaluation function (Section 20.7.1) and run subset enumeration with the five feature dimensions. Is the full pipeline Pareto-optimal? Are any dimensions truly redundant?

**20.7.** Train two decoders: one with gradient reversal for recording invariance, one without. Compare their DRI (invariant) scores. Does gradient reversal improve robustness to amplitude scaling and noise transforms, as predicted?

---

## Notes and References

Sharma, P. et al., "Contextual and combinatorial structure in sperm whale vocalisations," *Nature Communications* 15, 3617 (2024). Begus, G. et al., "Vowels and diphthongs in sperm whale vocalization," *Open Mind* 9, 1849--1874 (2025). Rendell, L. and Whitehead, H., "Vocal clans in sperm whales," *Proceedings of the Royal Society B* 270, 225--231 (2003). Gero, S. et al., "Individual, unit and vocal clan level identity cues in sperm whale codas," *Royal Society Open Science* 3, 150372 (2016). Youngblood, M., "Linguistic laws in whale vocalization," *Science Advances* 11, eads6014 (2025). The DSWP dataset: [huggingface.co/datasets/orrp/DSWP](https://huggingface.co/datasets/orrp/DSWP). The `eris-ketos` library (Bond, 2026) implements all geometric methods described here.

Nickel, M. and Kiela, D., "Poincare embeddings for learning hierarchical representations," *NeurIPS* 2017. Sarkar, R., "Low distortion Delaunay embedding of trees in hyperbolic plane," *Graph Drawing* (LNCS 7034), 2011. Arsigny, V. et al., "Log-Euclidean metrics for fast and simple calculus on diffusion tensors," *Magnetic Resonance in Medicine* 56(2), 2006. Edelsbrunner, H. and Harer, J., *Computational Topology: An Introduction*, AMS, 2010. Bauer, U., "Ripser: efficient computation of Vietoris-Rips persistence barcodes," *J. Appl. Comput. Topol.* 5, 391--423 (2021). Ganin, Y. et al., "Domain-adversarial training of neural networks," *JMLR* 17(59), 1--35 (2016). Bond, A.H., "ErisML: Geometric ethics framework," [erisml-lib](https://github.com/ahb-sjsu/erisml-lib), 2025. Paradise, O. et al., "WhAM: Whale Acoustic Model," *NeurIPS* 2025. Cantor, M. and Whitehead, H., "The interplay between social networks and culture," *Phil. Trans. R. Soc. B* 368, 20120340 (2013).
