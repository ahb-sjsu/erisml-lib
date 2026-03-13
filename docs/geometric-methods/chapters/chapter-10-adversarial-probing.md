# Chapter 10: Adversarial Probing

> *"The best way to understand a system is to try to break it---and then listen carefully to the sound it makes."*
> --- Attributed to Richard Hamming

The Model Robustness Index developed in Chapter 9 answers a critical question: *how stable is this configuration under random perturbation?* But random perturbation is blunt. It tells you that a model is fragile without telling you *why*, and it tells you that a model is robust without telling you *to what*. This chapter sharpens the MRI into a family of directed probing tools that interrogate model internals with the precision of a radar system. Where Chapter 9 threw noise at a model and measured the aggregate response, this chapter sends *specific, controlled signals* and reads the reflections.

We develop this idea into three concrete tools: the StructureProbe scanner (Section 10.3), parametric intensity sweeps (Section 10.4), and compositional interaction testing (Section 10.5). Section 10.6 then shows how the same mathematical framework extends from parameter-space fuzzing to signal-space fuzzing through the Decoder Robustness Index (DRI), applying MRI principles to acoustic decoders where semantic distance replaces raw error.

---

## 10.1 The Radar Analogy

### 10.1.1 From Physical Radar to Computational Probing

A radar transmitter emits a pulse of known shape $s(t)$. The environment reflects it, and the receiver records $r(t)$. The object of interest is the *transfer function* $H$ such that $r = H(s)$. By sweeping the frequency of $s$ and recording the response, the radar constructs a spectral signature of the target.

Adversarial probing replaces the electromagnetic pulse with a parametric perturbation and the physical environment with a computational model. The perturbation transform $T_\alpha$ takes an input and returns a modified version at intensity $\alpha \in [0, 1]$. The *probing displacement* is:

$$\delta(\alpha) = d\bigl(M(x),\; M(T_\alpha(x))\bigr)$$

where $d$ is an appropriate distance function---$L^2$ norm in representation space, MAE in prediction space, or semantic distance in classification space. The function $\delta : [0, 1] \to \mathbb{R}_{\geq 0}$ is the *intensity-response curve*, and its shape encodes the model's structural relationship to the perturbation.

### 10.1.2 Reading the Reflection Profile

Three canonical profiles emerge across domains:

**Flat profile** ($\delta(\alpha) \approx 0$ for all $\alpha$). The model is invariant to the perturbation. Desirable for structural invariants; alarming for stress transforms (the model is not reading the content being destroyed).

**Threshold profile** ($\delta(\alpha) \approx 0$ for $\alpha < \alpha^*$, then sharp rise). The model tolerates perturbation up to a critical intensity $\alpha^*$---the *adversarial threshold*. Binary search finds $\alpha^*$ efficiently.

**Linear profile** ($\delta(\alpha) \approx k\alpha$). Proportional degradation with no hidden tipping points---the most benign failure mode.

### 10.1.3 Invariance and Sensitivity as Structural Signatures

Transforms divide into *invariant* (semantics-preserving) and *stress* (semantics-destroying), a domain-dependent classification:

In parameter-space fuzzing (Chapter 9):

- **Invariant perturbations** are small multiplicative shifts. A model robust to 10% parameter variation occupies a broad minimum---desirable for deployment.
- **Stress perturbations** are large directional shifts or dimension ablations. A model that does not respond when an entire feature group is deactivated has not learned to use that group.

In acoustic decoder testing (Section 10.5):

- **Invariant transforms** include amplitude scaling and circular time shifts. A correct decoder should recognize the same coda regardless of recording volume or temporal alignment.
- **Stress transforms** include Doppler shift, multipath echo, and click dropout. These degrade the signal in ways that may legitimately change the decoder's output.

The *sensitivity gap*---the ratio of mean displacement under stress transforms to mean displacement under invariant transforms---is a single scalar that captures how well the model separates structural content from surface variation. A large gap indicates a model that has learned the domain's meaningful invariances; a small gap indicates a model that confuses structure with surface.

---

## 10.2 Parametric Transforms: The Intensity-Zero Identity

### 10.2.1 The Design Principle

Every parametric transform must satisfy one non-negotiable property:

> **Intensity-zero identity.** For all inputs $x$: $T(x, 0) = x$. At zero intensity, the transform is the identity.

This guarantees $\delta(0) = 0$, providing a calibrated baseline. The `AcousticTransform` class encapsulates this:

```python
@dataclass
class AcousticTransform:
    """Parametric transform with controllable intensity."""
    name: str
    fn: Callable[[np.ndarray, int, float], np.ndarray]
    intensity_range: tuple[float, float] = (0.0, 1.0)
    is_invariant: bool = True

    def __call__(self, signal, sr=32000, intensity=1.0):
        clamped = max(self.intensity_range[0],
                      min(self.intensity_range[1], intensity))
        return self.fn(signal, sr, clamped)

    def at_intensity(self, intensity):
        """Return a fixed-intensity closure for composition."""
        return lambda signal, sr: self(signal, sr, intensity)
```

The `at_intensity` method returns a closure with fixed perturbation strength, enabling composition into chains (Section 10.5) or integration with higher-order functions.

### 10.2.2 Intensity Sweeps

The most informative single measurement is the *intensity sweep*: evaluating the model's response at uniformly spaced levels from 0 to 1:

```python
def intensity_sweep(self, decoder, signals, sr, transform, n_points=10):
    """Sweep intensity from 0 to 1, recording mean omega at each level."""
    curve = []
    for intensity in np.linspace(0, 1, n_points):
        result = self.measure_single_transform(
            decoder, signals, sr, transform, float(intensity)
        )
        curve.append((float(intensity), result.mean_omega))
    return curve
```

Plotting all transform sweeps on a single figure produces the model's *sensitivity fingerprint*---a visual summary revealing which transforms the model tolerates, which it resists, and at what intensities transitions occur.

### 10.2.3 Adversarial Threshold Search

Where the sweep gives a coarse picture, binary search finds the exact threshold:

```python
def find_adversarial_threshold(self, decoder, signal, sr, transform,
                                tolerance=0.01):
    """Binary search for minimal intensity that flips the output."""
    baseline = decoder.classify(signal, sr)

    def causes_flip(intensity):
        transformed = transform(signal, sr, intensity)
        return decoder.classify(transformed, sr).strip().lower() \
               != baseline.strip().lower()

    if not causes_flip(1.0):
        return 1.0

    low, high = 0.0, 1.0
    while high - low > tolerance:
        mid = (low + high) / 2
        if causes_flip(mid):
            high = mid
        else:
            low = mid
    return high
```

A threshold of 0.95 means near-total robustness; 0.05 means the faintest perturbation flips the answer. The algorithm is identical to Chapter 9's parameter-space adversarial search---binary search on a monotone predicate finds the transition in $O(\log(1/\epsilon))$ evaluations regardless of domain.

---

## 10.3 StructureProbe: The Probe Response Matrix

### 10.3.1 The Measurement Protocol

Given a model $M$, an input corpus $\{x_1, \ldots, x_N\}$, and $K$ parametric transforms, the StructureProbe scanner constructs a $K \times J$ *probe response matrix* where entry $(k, j)$ is the mean displacement when transform $T_k$ is applied at intensity $\alpha_j$:

$$\bar{\delta}_{kj} = \frac{1}{N} \sum_{i=1}^{N} d\bigl(M(x_i),\; M(T_k(x_i, \alpha_j))\bigr)$$

Each row is an intensity-response curve. Each column is a cross-transform sensitivity snapshot.

### 10.3.2 From Ablation to Graded Perturbation

Chapter 9's sensitivity profile ablates each dimension (on/off). The probe response matrix generalizes this to *graded* perturbation. For dimension $i$ with baseline value $\theta_i$, define:

$$T_i(\theta, \alpha) = \theta \text{ with } \theta_i \leftarrow \theta_i \cdot e^{\alpha \cdot \sigma}$$

The intensity-response curve $\delta_i(\alpha) = |\text{MAE}(T_i(\theta, \alpha)) - \text{MAE}(\theta)|$ traces how error evolves as dimension $i$ is progressively perturbed:

```python
def probe_response_matrix(params, dim_names, evaluate_fn,
                          n_intensities=11, scale=2.0):
    """Compute (n_dims, n_intensities) displacement matrix."""
    intensities = np.linspace(0, 1, n_intensities)
    matrix = np.zeros((len(dim_names), n_intensities))
    base_mae, _ = evaluate_fn(params)

    for i in range(len(dim_names)):
        for j, alpha in enumerate(intensities):
            perturbed = params.copy()
            perturbed[i] = params[i] * np.exp(alpha * scale)
            perturbed[i] = np.clip(perturbed[i], 0.001, 1e6)
            pert_mae, _ = evaluate_fn(perturbed)
            matrix[i, j] = abs(pert_mae - base_mae)
    return matrix
```

### 10.3.3 Topological Analysis of Probe Surfaces

When the probe response matrix is analyzed with persistent homology (Chapter 5), additional structure emerges. Treating the matrix as a height function on a grid, the Vietoris-Rips complex reveals connected components (clusters of transforms with similar profiles) and loops (closed sensitivity circuits suggesting redundancy in the transform library). This connection---TDA applied to the outputs of adversarial probing---is a key integrative theme: geometric tools analyzing the results of other geometric tools.

---

## 10.4 Compositional Testing: Probing Dimension Interactions

### 10.4.1 Beyond Single-Dimension Probing

The probe response matrix perturbs one dimension at a time, revealing *marginal* sensitivity but missing *interactions*. Two dimensions might individually show low sensitivity but produce catastrophic failure when perturbed simultaneously---the parameter-space analogue of drug interactions in pharmacology.

Exhaustive pairwise probing (testing all $\binom{n}{2}$ dimension pairs at multiple intensities) is feasible for small $n$ but scales quadratically. For larger problems, the compositional testing framework provides a structured alternative that reveals the most important interactions without exhaustive search.

### 10.4.2 Greedy Dimension-Building Sequences

The `compositional_test` function builds dimension subsets incrementally, revealing interactions:

```python
from structural_fuzzing.compositional import compositional_test

result = compositional_test(
    start_dim=0,
    candidate_dims=[1, 2, 3, 4],
    dim_names=["Size", "Complexity", "Halstead", "OO", "Process"],
    evaluate_fn=evaluate_fn,
    n_grid=20,
    n_random=5000,
)

for i, (name, mae) in enumerate(
    zip(result.order_names, result.mae_sequence)
):
    print(f"Step {i}: add '{name}' -> MAE = {mae:.4f}")
```

At each step, the algorithm tries adding each remaining dimension, re-optimizes all parameters, and selects the dimension producing the greatest MAE reduction. The *interaction signature* is encoded in the step-to-step MAE differences. If $\text{MAE}_k - \text{MAE}_{k+1}$ exceeds the marginal sensitivity of $d_{k+1}$ alone, there is a positive interaction. If it falls below, there is redundancy.

The trajectory's shape is diagnostic: steep initial descent means a few key dimensions dominate; gradual uniform descent means all dimensions contribute equally; plateau-then-drop indicates synergistic interactions detectable only through combinatorial probing.

### 10.4.3 Transform Chains in Signal Space

The compositional principle extends to signal space through *transform chains*:

```python
class TransformChain:
    """Compose transforms for compound distortion testing."""
    def __init__(self, transforms: list[tuple[AcousticTransform, float]]):
        self.transforms = transforms
        self.name = " -> ".join(
            f"{t.name}@{i:.1f}" for t, i in transforms
        )

    def __call__(self, signal, sr=32000):
        result = signal.copy()
        for transform, intensity in self.transforms:
            result = transform(result, sr, intensity)
        return result
```

A chain like `noise@0.3 -> echo@0.6 -> doppler@0.4` applies three perturbations sequentially. Order matters: noise before echo gets echoed; noise after echo does not. The `TransformChain.generate_chains` factory produces diverse random chains:

```python
chains = TransformChain.generate_chains(
    transforms=transform_suite,
    max_length=3, intensities=[0.3, 0.6, 1.0],
    n_chains=50, seed=42,
)
```

A model that handles each individual transform at intensity 0.6 but fails under chains of length 2 at intensity 0.3 has a *superlinear interaction*---compound perturbation worse than the sum of its parts.

---

## 10.5 The Decoder Robustness Index: MRI for Signal Space

### 10.5.1 From Parameters to Signals

The DRI applies the MRI's mathematical structure to *input perturbation* rather than *parameter perturbation*. The formula carries over unchanged:

$$\text{DRI} = 0.5 \cdot \bar{\omega} + 0.3 \cdot P_{75}(\omega) + 0.2 \cdot P_{95}(\omega)$$

where each $\omega_i$ is now the displacement between baseline and perturbed predictions, and lower DRI indicates greater robustness.

### 10.5.2 Graduated Omega via Semantic Distance

The DRI's key innovation is *semantic distance* rather than binary match/mismatch. For a cetacean decoder classifying whale codas, misclassifying *rhythm* (fundamental structure) is worse than misclassifying *ornamentation* (fine detail):

```python
CODA_FEATURE_WEIGHTS = {
    "rhythm":        1.0,   # Fundamental timing pattern
    "tempo":         0.7,   # Overall speed
    "rubato":        0.4,   # Subtle timing variation
    "ornamentation": 0.2,   # Extra clicks, finest detail
}

class CodaSemanticDistance:
    """Semantic distance using coda feature hierarchy."""
    def __init__(self, feature_weights=None, coda_features=None):
        self.weights = feature_weights or CODA_FEATURE_WEIGHTS
        self.coda_features = coda_features or {}

    def distance(self, pred1, pred2):
        if pred1.strip().lower() == pred2.strip().lower():
            return 0.0
        feat1 = self.coda_features.get(pred1.strip())
        feat2 = self.coda_features.get(pred2.strip())
        if feat1 is not None and feat2 is not None:
            total_weight = sum(self.weights.values())
            mismatch_weight = sum(
                w for f, w in self.weights.items()
                if feat1.get(f) != feat2.get(f)
            )
            semantic_dist = mismatch_weight / total_weight
            return max(0.5, 0.5 + 0.5 * semantic_dist)
        return 0.75  # Fallback: binary mismatch
```

The hybrid formula---minimum 0.5 penalty for any flip, scaling to 1.0 for maximally different predictions---ensures the DRI never ignores a decision flip. An ornamentation change gets $\omega \approx 0.54$; a rhythm change gets $\omega \approx 0.93$. The graduated omega reflects the domain's feature hierarchy.

### 10.5.3 The Full DRI Pipeline

The `DecoderRobustnessIndex.measure` method orchestrates four phases---per-transform intensity sweeps, compositional chain testing, adversarial threshold search, and DRI computation---mirroring the structure of the `run_campaign` pipeline in the structural fuzzing framework:

```python
transforms = make_acoustic_transform_suite()
dri = DecoderRobustnessIndex(transforms)
result = dri.measure(decoder, signals, labels, sr=32000)
print(f"DRI: {result.dri:.4f}")
print(f"DRI (invariant): {result.dri_invariant:.4f}")
print(f"DRI (stress):    {result.dri_stress:.4f}")
```

The `DRIResult` provides three granularity levels:

1. **Scalar DRI.** A single number for cross-decoder comparison.
2. **DRI by category.** Separate values for invariant and stress transforms, revealing whether weaknesses lie in unlearned symmetries or over-sensitivity to legitimate distortion.
3. **Per-transform diagnostics.** Mean omega per transform, chain results, and adversarial thresholds---the full radar image.

### 10.5.4 The Acoustic Transform Suite

Nine transforms form the probing library, categorized by invariance expectation:

| Transform | Type | What It Tests |
|-----------|------|---------------|
| amplitude_scale | Invariant | Volume independence |
| time_shift | Invariant | Temporal alignment independence |
| additive_noise | Invariant | White noise tolerance |
| pink_noise | Invariant | Realistic ocean noise tolerance |
| doppler_shift | Stress | Frequency stability under motion |
| multipath_echo | Stress | Echo robustness |
| time_stretch | Stress | Tempo variation tolerance |
| spectral_mask | Stress | Bandwidth limitation robustness |
| click_dropout | Stress | Missing data robustness |

The `is_invariant` flag drives separate `dri_invariant` and `dri_stress` aggregation. A decoder with high `dri_invariant` has engineering defects. A decoder with high `dri_stress` may simply be doing its job---detecting genuine signal degradation.

---

## 10.6 Connection to the Structural Fuzzing Pipeline

### 10.6.1 The Six-Step Campaign

The structural fuzzing pipeline orchestrates all probing tools into a unified analysis:

```python
from structural_fuzzing.pipeline import run_campaign

report = run_campaign(
    dim_names=["Size", "Complexity", "Halstead", "OO", "Process"],
    evaluate_fn=evaluate_fn,
    max_subset_dims=4,
    n_mri_perturbations=300,
    adversarial_tolerance=0.5,
)
```

| Stage | Tool | Chapter | Question |
|-------|------|---------|----------|
| 1 | Subset enumeration | 4 | Which dimension combinations matter? |
| 2 | Pareto frontier | 5 | Which configurations are non-dominated? |
| 3 | Sensitivity profiling | 10 | Which dimensions drive predictions? |
| 4 | Model Robustness Index | 9 | How stable is the best configuration? |
| 5 | Adversarial thresholds | 10 | Where does each dimension break? |
| 6 | Compositional testing | 10 | How do dimensions interact? |

### 10.6.2 The Report as a Geometric Object

The `StructuralFuzzReport` returned by `run_campaign` is itself a geometric object. Its fields encode: a set of *points* in the (dimensions, MAE) plane (subset results), a *frontier* in this plane (Pareto-optimal configurations), a *vector* of importances (sensitivity profile), a *scalar* with supporting distribution (the MRI and its omega distribution), a set of *boundaries* in parameter space (adversarial thresholds), and a *path* through subset space (the compositional building sequence). Taken together, these define the geometric structure of the model's configuration space as explored by the probing campaign.

### 10.6.3 Portability of the Framework

The MRI/DRI mathematical structure is domain-agnostic. The specific transforms change, but the measurement protocol, aggregation formula, and diagnostic decomposition remain identical:

| Bond Index (Ethics) | DRI (Bioacoustics) | MRI (Structural Fuzzing) |
|---------------------|---------------------|--------------------------|
| Scenario transforms | Acoustic transforms | Parameter perturbations |
| Option semantic distance | Coda semantic distance | MAE deviation ($\omega$) |
| Graduated omega | Graduated omega | Continuous omega |
| Adversarial threshold | Adversarial threshold | Adversarial threshold |
| Compositional chains | Compositional chains | Compositional testing |

The common mathematical spine is:

$$\text{Index} = w_1 \cdot \bar{\omega} + w_2 \cdot P_{75}(\omega) + w_3 \cdot P_{95}(\omega)$$

with $\omega$ computed as domain-appropriate distance between baseline and perturbed outputs. The framework is a template instantiable for any domain where "perturbation," "output," and "distance" are well-defined.

---

## 10.7 Practical Considerations

### 10.7.1 Computational Budget

A full DRI measurement with 9 transforms, 3 intensity levels, 50 chains, and 100 signals requires approximately 7,800 model evaluations. Three strategies reduce cost: subsample the corpus (if the profile is stable at $N = 20$, use 20); reduce the intensity grid (3 levels captures most curves); and parallelize (transform evaluations are embarrassingly parallel).

### 10.7.2 Deterministic Seeding

All stochastic transforms are seeded from the input's content hash, ensuring identical perturbations across model comparisons and enabling differential analysis of model updates.

### 10.7.3 Choosing the Distance Function

The distance function must match the output space: $L^2$ norm for continuous outputs, semantic distance for classifications, edit distance for sequences. The DRI's graduated semantic distance is a general pattern for any classification domain where some errors are worse than others.

---

## 10.8 Summary and Forward Connections

### 10.8.1 What This Chapter Established

This chapter developed the adversarial probing framework:

1. **Parametric transforms** with the intensity-zero identity property.
2. **The StructureProbe scanner** producing probe response matrices---structural fingerprints under perturbation.
3. **Intensity sweeps and adversarial threshold search** for precise failure-boundary characterization.
4. **Compositional testing** via greedy dimension-building and transform chains, revealing interaction effects.
5. **The Decoder Robustness Index (DRI)** as MRI for signal-space perturbation with graduated semantic distance.
6. **Topological analysis** of probe surfaces using persistent homology (Chapter 5).

The unifying theme is the radar analogy: *the difference between "sent" and "received" encodes the structure of the system being probed*.

### 10.8.2 Connection to Part III

Part III shifts from developing tools in isolation to deploying them in integrated systems. The probing framework is central:

- **Chapter 11** applies probing to continuous monitoring, tracking how sensitivity fingerprints evolve and triggering alerts when adversarial thresholds drop.
- **Chapter 12** integrates probing with pathfinding (Chapter 6), navigating from fragile to robust configurations along geodesics using the probe response surface as the cost function.
- **Chapter 13** combines probing with multi-objective optimization, computing Pareto frontiers in the (MAE, DRI) plane to select configurations that are simultaneously accurate and robust.

The transition from Part II to Part III mirrors the transition from constructing individual instruments to building an orchestra. Each instrument---subset enumeration, Pareto analysis, sensitivity profiling, MRI, adversarial probing, TDA---has been developed and tested in isolation. Part III teaches them to play together.
