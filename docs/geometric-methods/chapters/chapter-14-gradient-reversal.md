# Chapter 14: Gradient Reversal and Invariance Training

> *"The encoder that remembers everything is the encoder that has learned nothing."*
> --- Paraphrase of a principle from domain adaptation theory

Chapter 9 introduced adversarial robustness testing: probing a model's behavior under perturbation to discover where and how it breaks. That methodology is *diagnostic*---it measures fragility after the fact. This chapter introduces a complementary technique that is *prescriptive*: gradient reversal training, which forces an encoder to become invariant to specified nuisance variables during training itself. Where Chapter 9 asks "does the model break when we push it?", this chapter asks "can we build a model that *cannot* encode information we do not want it to have?"

The motivation is immediate and practical. An encoder trained to classify sperm whale coda types from spectrograms will, left to its own devices, happily memorize the recording conditions---hydrophone frequency response, ambient noise spectrum, ocean reverberation profile---alongside the biological signal. It achieves excellent accuracy on the training set because the recording conditions are correlated with the deployment location, and the deployment location is correlated with the whale clan. The encoder has learned a shortcut: predict the clan, then predict the coda type. On a new hydrophone, deployed in a new ocean basin, this encoder fails catastrophically, because the shortcut no longer holds.

This is not a pathology specific to cetacean bioacoustics. It is the central problem of **domain adaptation**, and it arises whenever surface features are correlated with target labels in the training data but not in the deployment environment. The gradient reversal layer, introduced by Ganin and Lempitsky (2015) and developed further by Ganin et al. (2016), provides an elegant solution: attach an adversarial classifier to the encoder's latent representation, train it to predict the nuisance variable (recording conditions, domain identity, speaker identity), and then *reverse the gradient* flowing back through the encoder, so that the encoder is trained to make the adversarial classifier's job *impossible*. The result is a representation that is invariant to the nuisance variable by construction.

We begin with a precise statement of the invariance problem (Section 14.1), develop the gradient reversal layer and its training procedure (Section 14.2), give the geometric interpretation as projection onto the orthogonal complement of a nuisance subspace (Section 14.3), implement the full system in PyTorch (Section 14.4), apply it to cetacean bioacoustics (Section 14.5), connect to the adversarial robustness framework of Chapter 9 (Section 14.6), and close with forward connections to the group-theoretic augmentation methods of Chapter 15.

---

## 14.1 The Invariance Problem

### 14.1.1 Encoders That Memorize Surface Features

Consider an encoder $f_\theta : \mathcal{X} \to \mathcal{Z}$ that maps raw inputs (spectrograms, images, text) to a latent representation $\mathbf{z} = f_\theta(\mathbf{x}) \in \mathbb{R}^d$. A task classifier $g_\phi : \mathcal{Z} \to \mathcal{Y}$ then maps the representation to predictions. The standard training objective minimizes the task loss:

$$\mathcal{L}_{\text{task}}(\theta, \phi) = \mathbb{E}_{(\mathbf{x}, y) \sim \mathcal{D}}\left[\ell\big(g_\phi(f_\theta(\mathbf{x})), y\big)\right]$$

This objective says nothing about *what* the encoder should learn. It only demands that the composition $g_\phi \circ f_\theta$ produce correct predictions. The encoder is free to use any feature of the input that is predictive of the label---including features that are predictive only because of spurious correlations in the training data.

Formally, let $s \in \mathcal{S}$ be a **nuisance variable**---an attribute of the input that we do not want the encoder to depend on. In bioacoustics, $s$ might be the recording device, the ocean basin, or the time of year. In medical imaging, $s$ might be the scanner model or the hospital. In NLP, $s$ might be the author's dialect or the document's formatting.

The standard training objective places no constraint on the mutual information $I(\mathbf{z}; s)$ between the latent representation and the nuisance variable. If $s$ is correlated with $y$ in the training data, gradient descent will cheerfully exploit that correlation, producing an encoder for which $I(\mathbf{z}; s)$ is high. The encoder has memorized the surface features.

### 14.1.2 The Domain Shift Failure Mode

The consequence of high $I(\mathbf{z}; s)$ is predictable: when the correlation between $s$ and $y$ breaks down---because the model is deployed on a new domain, a new device, or a new population---the encoder's predictions degrade. This is **domain shift**, and it is one of the most common failure modes in applied machine learning.

The structural fuzzing framework of Chapter 9 can *detect* this failure mode after training. The Decoder Robustness Index (DRI), adapted from the Bond Index, applies parametric acoustic transforms at varying intensities and measures how the decoder's output changes:

```python
# From eris_ketos.decoder_robustness — diagnosis after the fact
dri = DecoderRobustnessIndex(transforms)
result = dri.measure(decoder, signals, labels, sr=32000)
# result.per_transform reveals which transforms cause the most drift
```

The DRI tells you *that* the model is sensitive to recording conditions. Gradient reversal tells the model *not to be*.

### 14.1.3 The Invariance Objective

The goal is to learn a representation $\mathbf{z} = f_\theta(\mathbf{x})$ such that:

1. **Task performance**: $\mathbf{z}$ is highly predictive of the target label $y$.
2. **Nuisance invariance**: $\mathbf{z}$ is *not* predictive of the nuisance variable $s$.

In information-theoretic terms, we want to maximize $I(\mathbf{z}; y)$ while minimizing $I(\mathbf{z}; s)$. These objectives are in tension whenever $y$ and $s$ are correlated. The gradient reversal layer resolves this tension through adversarial training.

---

## 14.2 The Gradient Reversal Layer

### 14.2.1 Architecture

The domain-adversarial neural network (DANN) architecture, introduced by Ganin et al. (2016), augments the standard encoder-classifier pair with a **domain discriminator** $h_\psi : \mathcal{Z} \to \mathcal{S}$ that attempts to predict the nuisance variable from the latent representation:

```
                          ┌──────────────┐
                          │ Task Head    │
                   ┌─────>│ g_φ(z) → y   │
                   │      └──────────────┘
┌──────────┐      │
│ Encoder  │──z──>│
│ f_θ(x)   │      │      ┌──────────────┐
└──────────┘      │  GRL  │ Domain Head  │
                   └──×──>│ h_ψ(z) → s   │
                          └──────────────┘
```

The key innovation is the **gradient reversal layer (GRL)**, denoted by the $\times$ symbol in the diagram. During the forward pass, the GRL is the identity function: it passes $\mathbf{z}$ through unchanged. During the backward pass, it *negates* the gradient:

$$\text{GRL}(\mathbf{z}) = \mathbf{z} \quad \text{(forward)}$$
$$\frac{\partial \text{GRL}}{\partial \mathbf{z}} = -\lambda \mathbf{I} \quad \text{(backward)}$$

where $\lambda > 0$ is a scaling factor that controls the strength of the adversarial signal.

### 14.2.2 The Combined Loss

The full training objective is:

$$\mathcal{L}(\theta, \phi, \psi) = \mathcal{L}_{\text{task}}(\theta, \phi) - \lambda \, \mathcal{L}_{\text{domain}}(\theta, \psi)$$

where:
- $\mathcal{L}_{\text{task}}$ is the standard task loss (e.g., cross-entropy for classification).
- $\mathcal{L}_{\text{domain}}$ is the domain discriminator's loss (also typically cross-entropy).
- $\lambda$ controls the tradeoff between task performance and domain invariance.

The sign convention is critical. The domain discriminator parameters $\psi$ are trained to *minimize* $\mathcal{L}_{\text{domain}}$---the discriminator gets better at predicting the nuisance variable. But the encoder parameters $\theta$ receive the *negated* gradient from $\mathcal{L}_{\text{domain}}$, so they are trained to *maximize* it---the encoder gets better at fooling the discriminator.

This is a minimax game:

$$\min_{\theta, \phi} \max_\psi \; \mathcal{L}_{\text{task}}(\theta, \phi) - \lambda \, \mathcal{L}_{\text{domain}}(\theta, \psi)$$

At equilibrium, the domain discriminator performs at chance level: the latent representation contains no information about the nuisance variable, so no classifier can predict it above baseline.

### 14.2.3 Why Not Just Remove the Nuisance Variable?

A natural question: why not simply remove the nuisance variable from the input? If recording conditions are the problem, preprocess the audio to normalize them.

The answer is that nuisance variables are rarely cleanly separable from the signal of interest. A hydrophone's frequency response shapes the spectrogram globally---it is not a feature you can mask out. Ocean reverberation creates echoes that overlap with the biological signal. Ambient noise occupies the same frequency bands as whale clicks. The nuisance and the signal are *entangled* in the input, and no preprocessing step can disentangle them without also removing biological information.

Gradient reversal operates at the representation level, where the entanglement has been partially resolved by the encoder's learned features. The adversarial training forces the encoder to resolve the entanglement *further*, retaining the biological information while discarding the recording-condition information. This is a strictly more powerful approach than input-level preprocessing, because the encoder can learn nonlinear disentanglements that no fixed preprocessing pipeline can express.

---

## 14.3 The Geometric Interpretation

### 14.3.1 The Latent Space as a Vector Space

The latent representation $\mathbf{z} \in \mathbb{R}^d$ lives in a $d$-dimensional vector space. Within this space, we can identify two subspaces:

- **The task subspace** $\mathcal{V}_{\text{task}} \subseteq \mathbb{R}^d$: the directions along which $\mathbf{z}$ varies in ways that are predictive of $y$.
- **The nuisance subspace** $\mathcal{V}_{\text{nuis}} \subseteq \mathbb{R}^d$: the directions along which $\mathbf{z}$ varies in ways that are predictive of $s$.

If these subspaces are orthogonal ($\mathcal{V}_{\text{task}} \perp \mathcal{V}_{\text{nuis}}$), the invariance problem is trivial: project onto $\mathcal{V}_{\text{task}}$ and discard $\mathcal{V}_{\text{nuis}}$. The difficulty arises when the subspaces overlap---when some directions in $\mathbb{R}^d$ are simultaneously predictive of both $y$ and $s$. This overlap is precisely the "entanglement" described in Section 14.2.3.

### 14.3.2 Gradient Reversal as Orthogonal Projection

The geometric insight behind gradient reversal is this: the reversed gradient pushes the encoder to produce representations that lie in the **orthogonal complement** of the nuisance subspace.

Consider the gradient of the domain loss with respect to the encoder's output:

$$\mathbf{g}_{\text{domain}} = \nabla_{\mathbf{z}} \mathcal{L}_{\text{domain}}$$

This gradient points in the direction that would make $\mathbf{z}$ *more* predictive of the nuisance variable $s$. It lies in (or near) $\mathcal{V}_{\text{nuis}}$. The gradient reversal layer negates this:

$$\mathbf{g}_{\text{reversed}} = -\lambda \, \nabla_{\mathbf{z}} \mathcal{L}_{\text{domain}}$$

The encoder thus receives a combined gradient signal:

$$\mathbf{g}_{\text{total}} = \nabla_{\mathbf{z}} \mathcal{L}_{\text{task}} - \lambda \, \nabla_{\mathbf{z}} \mathcal{L}_{\text{domain}}$$

The first term pulls the representation toward $\mathcal{V}_{\text{task}}$. The second term pushes it away from $\mathcal{V}_{\text{nuis}}$. At convergence, the representation has been projected onto $\mathcal{V}_{\text{task}} \cap \mathcal{V}_{\text{nuis}}^\perp$---the subspace that is predictive of the task but orthogonal to the nuisance directions.

### 14.3.3 Connection to SPD Manifolds

When the features of interest are covariance matrices---as they are for the SPD spectral analysis of Chapter 4---the geometry becomes Riemannian rather than Euclidean. Recall from Chapter 4 that frequency-band covariance matrices live on the SPD manifold $\text{SPD}(n)$, with the log-Euclidean metric:

$$d_{\text{LE}}(\Sigma_1, \Sigma_2) = \|\log(\Sigma_1) - \log(\Sigma_2)\|_F$$

In this setting, the gradient reversal layer operates on the tangent space of the SPD manifold at the current covariance estimate. The log-Euclidean map sends SPD matrices to symmetric matrices (the tangent space), where the orthogonal complement construction applies directly. The encoder is trained to produce covariance features whose tangent-space coordinates are orthogonal to the nuisance directions.

Concretely, the `SPDManifold.log_map` from `eris_ketos.spd_spectral` maps the covariance matrix to tangent space, the gradient reversal operates in that tangent space, and `SPDManifold.exp_map` maps back:

```python
from eris_ketos.spd_spectral import SPDManifold

# In tangent space, standard linear operations apply
log_cov = SPDManifold.log_map(cov_matrix)   # SPD -> symmetric
# ... gradient reversal operates here, in tangent space ...
cov_invariant = SPDManifold.exp_map(log_cov) # symmetric -> SPD
```

This connection is not incidental. The reason gradient reversal generalizes cleanly to non-Euclidean settings is precisely that it operates on gradients---tangent vectors---and tangent spaces are always (locally) Euclidean, regardless of the curvature of the ambient manifold.

### 14.3.4 The Rank of the Nuisance Subspace

An important practical question is: how many dimensions does the nuisance subspace occupy? If the nuisance variable $s$ is low-dimensional (e.g., a binary domain label), the nuisance subspace $\mathcal{V}_{\text{nuis}}$ is typically low-rank, and gradient reversal can eliminate it without significantly reducing the encoder's capacity for the task.

But if the nuisance variable is high-dimensional (e.g., a full characterization of recording conditions including hydrophone response, noise spectrum, reverberation profile, and depth), $\mathcal{V}_{\text{nuis}}$ may span many directions in $\mathbb{R}^d$, and the orthogonal complement $\mathcal{V}_{\text{nuis}}^\perp$ may have insufficient capacity for the task. In this case, the $\lambda$ parameter mediates a genuine tradeoff: higher $\lambda$ forces stronger invariance at the cost of task performance.

The structural fuzzing framework provides a direct way to diagnose this tradeoff. After training with gradient reversal, apply the DRI from Chapter 9 to measure residual sensitivity to each nuisance dimension. If the DRI for a particular transform (e.g., `amplitude_scale` or `additive_noise`) remains high despite gradient reversal training, the corresponding nuisance direction is entangled with the task subspace in a way that gradient reversal alone cannot resolve.

---

## 14.4 Implementation

### 14.4.1 The Gradient Reversal Layer in PyTorch

The gradient reversal layer is remarkably simple to implement. The key mechanism is PyTorch's `autograd.Function`, which allows custom forward and backward behavior:

```python
import torch
import torch.nn as nn
from torch.autograd import Function


class GradientReversalFn(Function):
    """Reverses gradients during backpropagation.

    Forward pass: identity.
    Backward pass: negate and scale by lambda.
    """

    @staticmethod
    def forward(ctx, x: torch.Tensor, lambda_: float) -> torch.Tensor:
        ctx.lambda_ = lambda_
        return x.clone()

    @staticmethod
    def backward(ctx, grad_output: torch.Tensor):
        return -ctx.lambda_ * grad_output, None


class GradientReversalLayer(nn.Module):
    """Module wrapper for gradient reversal.

    Args:
        lambda_: Scaling factor for reversed gradients.
                 Higher values enforce stronger invariance.
    """

    def __init__(self, lambda_: float = 1.0) -> None:
        super().__init__()
        self.lambda_ = lambda_

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return GradientReversalFn.apply(x, self.lambda_)

    def set_lambda(self, lambda_: float) -> None:
        """Update lambda (e.g., on a schedule during training)."""
        self.lambda_ = lambda_
```

The implementation is five lines of computational logic wrapped in PyTorch's autograd machinery. The `forward` method is the identity (with a `clone()` to ensure a clean computational graph). The `backward` method negates the gradient and scales by $\lambda$. That is all gradient reversal *is*.

### 14.4.2 The Domain-Adversarial Network

The full architecture composes the encoder, task head, gradient reversal layer, and domain head:

```python
class DomainAdversarialNetwork(nn.Module):
    """Domain-adversarial neural network (DANN) for invariance training.

    Architecture:
        input -> encoder -> z -> task_head -> task prediction
                              |
                              +-> GRL -> domain_head -> domain prediction

    Args:
        encoder: Feature extractor mapping inputs to latent vectors.
        task_head: Classifier for the primary task.
        domain_head: Classifier for the nuisance variable.
        lambda_: Initial gradient reversal strength.
    """

    def __init__(
        self,
        encoder: nn.Module,
        task_head: nn.Module,
        domain_head: nn.Module,
        lambda_: float = 1.0,
    ) -> None:
        super().__init__()
        self.encoder = encoder
        self.task_head = task_head
        self.domain_head = domain_head
        self.grl = GradientReversalLayer(lambda_)

    def forward(
        self, x: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass returning both task and domain predictions.

        Args:
            x: Input tensor.

        Returns:
            Tuple of (task_logits, domain_logits).
        """
        z = self.encoder(x)
        task_logits = self.task_head(z)
        domain_logits = self.domain_head(self.grl(z))
        return task_logits, domain_logits
```

### 14.4.3 The Lambda Schedule

A critical practical detail is the **lambda schedule**. Starting with a large $\lambda$ destabilizes training: the adversarial signal overwhelms the task gradient before the encoder has learned any useful features. Ganin et al. recommend a schedule that ramps $\lambda$ from 0 to its maximum value over the course of training:

$$\lambda(p) = \frac{2}{1 + \exp(-\gamma \cdot p)} - 1$$

where $p \in [0, 1]$ is the training progress (fraction of total epochs completed) and $\gamma$ controls the ramp rate. This is a sigmoid schedule: $\lambda(0) \approx 0$, $\lambda(1) \approx 1$.

```python
def lambda_schedule(
    epoch: int,
    total_epochs: int,
    gamma: float = 10.0,
    max_lambda: float = 1.0,
) -> float:
    """Sigmoid ramp schedule for gradient reversal strength.

    Starts near zero, ramps to max_lambda over training.
    Early epochs focus on learning useful features;
    later epochs enforce invariance.

    Args:
        epoch: Current epoch (0-indexed).
        total_epochs: Total number of training epochs.
        gamma: Ramp steepness (higher = sharper transition).
        max_lambda: Maximum lambda value at end of training.

    Returns:
        Lambda value for this epoch.
    """
    import math

    p = epoch / max(total_epochs - 1, 1)
    return max_lambda * (2.0 / (1.0 + math.exp(-gamma * p)) - 1.0)
```

The schedule ensures that the encoder first learns discriminative features for the task (when $\lambda \approx 0$), and only later is forced to discard nuisance information (as $\lambda$ ramps up). Without this schedule, gradient reversal training is notoriously unstable.

### 14.4.4 The Training Loop

The training loop for domain-adversarial training is structurally similar to standard supervised training, with two loss terms and a lambda schedule:

```python
def train_dann(
    model: DomainAdversarialNetwork,
    train_loader: torch.utils.data.DataLoader,
    optimizer: torch.optim.Optimizer,
    task_criterion: nn.Module,
    domain_criterion: nn.Module,
    total_epochs: int,
    gamma: float = 10.0,
    max_lambda: float = 1.0,
    device: torch.device = torch.device("cpu"),
) -> dict[str, list[float]]:
    """Train a DANN with gradient reversal.

    Each batch yields (inputs, task_labels, domain_labels).
    The domain_labels encode the nuisance variable (e.g., recording
    device ID, ocean basin, hydrophone type).

    Returns:
        Dictionary of training curves (task_loss, domain_loss,
        domain_accuracy per epoch).
    """
    history: dict[str, list[float]] = {
        "task_loss": [],
        "domain_loss": [],
        "domain_accuracy": [],
    }

    for epoch in range(total_epochs):
        # Update lambda on schedule
        lam = lambda_schedule(epoch, total_epochs, gamma, max_lambda)
        model.grl.set_lambda(lam)

        epoch_task_loss = 0.0
        epoch_domain_loss = 0.0
        domain_correct = 0
        domain_total = 0

        model.train()
        for inputs, task_labels, domain_labels in train_loader:
            inputs = inputs.to(device)
            task_labels = task_labels.to(device)
            domain_labels = domain_labels.to(device)

            task_logits, domain_logits = model(inputs)

            loss_task = task_criterion(task_logits, task_labels)
            loss_domain = domain_criterion(domain_logits, domain_labels)

            # Combined loss: task + domain (GRL handles sign for encoder)
            loss = loss_task + loss_domain

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_task_loss += loss_task.item() * inputs.size(0)
            epoch_domain_loss += loss_domain.item() * inputs.size(0)
            domain_correct += (
                domain_logits.argmax(dim=1) == domain_labels
            ).sum().item()
            domain_total += inputs.size(0)

        n = domain_total or 1
        history["task_loss"].append(epoch_task_loss / n)
        history["domain_loss"].append(epoch_domain_loss / n)
        history["domain_accuracy"].append(domain_correct / n)

    return history
```

Note a subtle but important point in the combined loss: we write `loss = loss_task + loss_domain`, *not* `loss = loss_task - lambda * loss_domain`. The sign reversal is handled by the GRL, which negates the gradient flowing from `loss_domain` back through the encoder. The domain head's own parameters receive the *un-reversed* gradient and are trained normally to minimize the domain classification loss. This asymmetry---the same loss term trains the domain head to succeed and the encoder to make it fail---is the essence of the adversarial game.

### 14.4.5 Monitoring Convergence

The diagnostic signature of successful gradient reversal training is:

1. **Task loss decreases** throughout training (the encoder learns useful features).
2. **Domain accuracy drops to chance level** as $\lambda$ ramps up (the encoder becomes invariant).
3. **Domain loss increases** (the domain discriminator cannot predict the nuisance variable).

If the domain accuracy does not decrease, $\lambda$ is too small or the domain head is too weak. If the task loss increases sharply when $\lambda$ ramps up, the nuisance subspace overlaps significantly with the task subspace, and $\max\_\lambda$ should be reduced. The interplay between these curves provides real-time geometric diagnostics: the system is searching for the orthogonal complement of the nuisance subspace, and the curves tell you whether that complement has sufficient capacity for the task.

---

## 14.5 Application: Cetacean Bioacoustics

### 14.5.1 The Recording Condition Problem

Cetacean bioacoustics presents a textbook case for gradient reversal. The field data collection pipeline introduces systematic variation that is correlated with, but not caused by, the biological signal:

| Nuisance Factor | Source | Effect on Spectrogram |
|---|---|---|
| Hydrophone response | Equipment variation | Frequency-dependent gain/attenuation |
| Ocean depth | Deployment geometry | Reverberation pattern, multipath delay |
| Ambient noise | Weather, ship traffic | Broadband masking, SNR variation |
| Recording gain | Operator settings | Overall amplitude scaling |
| Sample rate | Equipment generation | Bandwidth truncation |

The `acoustic_transforms` module in `eris_ketos` parameterizes exactly these nuisance factors as intensity-controllable transforms. Chapter 9 used them for post-hoc robustness testing. Here we use the same taxonomy to define the nuisance variable for invariance training.

### 14.5.2 Architecture for Invariant Coda Classification

The architecture for invariant coda classification follows the DANN template:

```python
class CodaEncoder(nn.Module):
    """Spectrogram encoder for coda classification.

    Extracts latent features from mel spectrograms. The architecture
    follows a standard convolutional design, producing a fixed-length
    feature vector from variable-length inputs via global average pooling.
    """

    def __init__(self, n_mels: int = 128, latent_dim: int = 128) -> None:
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),
        )
        self.fc = nn.Linear(128, latent_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Encode spectrogram to latent vector.

        Args:
            x: Mel spectrogram, shape [batch, 1, n_mels, n_frames].

        Returns:
            Latent vector, shape [batch, latent_dim].
        """
        h = self.conv(x).squeeze(-1).squeeze(-1)
        return self.fc(h)


class CodaTaskHead(nn.Module):
    """Coda type classifier (primary task)."""

    def __init__(self, latent_dim: int = 128, n_classes: int = 23) -> None:
        super().__init__()
        self.head = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, n_classes),
        )

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        return self.head(z)


class RecordingConditionHead(nn.Module):
    """Recording condition discriminator (adversarial head).

    Predicts nuisance label from latent features. Designed to be
    "strong enough" to detect domain information if present, but
    not so large that it dominates the encoder's capacity.
    """

    def __init__(
        self, latent_dim: int = 128, n_conditions: int = 5
    ) -> None:
        super().__init__()
        self.head = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, n_conditions),
        )

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        return self.head(z)
```

The domain head is deliberately smaller than the task head. This is a design choice, not an oversight. A domain head that is too powerful can extract nuisance information from subtle correlations in the latent space that a simpler head would miss, leading to an unstable minimax game. A moderately sized domain head provides a sufficient invariance signal without the pathological dynamics of an overpowered adversary.

### 14.5.3 Assembling and Training the Invariant Classifier

```python
def build_invariant_coda_classifier(
    n_mels: int = 128,
    latent_dim: int = 128,
    n_coda_types: int = 23,
    n_conditions: int = 5,
    max_lambda: float = 0.5,
) -> DomainAdversarialNetwork:
    """Build a DANN for recording-invariant coda classification.

    Args:
        n_mels: Number of mel frequency bins.
        latent_dim: Encoder output dimensionality.
        n_coda_types: Number of coda type classes.
        n_conditions: Number of recording condition categories.
        max_lambda: Maximum gradient reversal strength.

    Returns:
        DomainAdversarialNetwork ready for training.
    """
    encoder = CodaEncoder(n_mels=n_mels, latent_dim=latent_dim)
    task_head = CodaTaskHead(latent_dim=latent_dim, n_classes=n_coda_types)
    domain_head = RecordingConditionHead(
        latent_dim=latent_dim, n_conditions=n_conditions
    )

    return DomainAdversarialNetwork(
        encoder=encoder,
        task_head=task_head,
        domain_head=domain_head,
        lambda_=0.0,  # Starts at zero; ramped by schedule
    )
```

### 14.5.4 Integrating SPD Features

The SPD spectral features from Chapter 4 provide a natural complement to the raw spectrogram encoder. The frequency-band covariance matrix captures inter-band correlations---harmonic relationships, resonance structure---that the spectrogram encoder might miss. But covariance matrices are particularly susceptible to recording-condition contamination: the hydrophone's frequency response multiplies into every off-diagonal entry.

Gradient reversal on SPD features requires operating in the tangent space, as described in Section 14.3.3:

```python
from eris_ketos.spd_spectral import SPDManifold, compute_covariance


class SPDInvariantEncoder(nn.Module):
    """Encoder that maps SPD covariance features through gradient reversal.

    Operates in the log-Euclidean tangent space where standard linear
    operations (and therefore gradient reversal) apply correctly.
    """

    def __init__(self, n_bands: int = 16, latent_dim: int = 64) -> None:
        super().__init__()
        # Upper triangle of n_bands x n_bands symmetric matrix
        spd_feature_dim = n_bands * (n_bands + 1) // 2
        self.encoder = nn.Sequential(
            nn.Linear(spd_feature_dim, 128),
            nn.ReLU(),
            nn.Linear(128, latent_dim),
        )

    def forward(self, spd_features: torch.Tensor) -> torch.Tensor:
        """Encode log-Euclidean SPD features.

        Args:
            spd_features: Upper-triangle features from log(cov),
                         shape [batch, n_bands*(n_bands+1)/2].

        Returns:
            Latent vector, shape [batch, latent_dim].
        """
        return self.encoder(spd_features)
```

The SPD features arrive already in tangent space (via `spd_features_from_spectrogram`, which applies the log map and extracts the upper triangle). The gradient reversal layer operates on the encoder's output, which is a standard Euclidean vector. This is the key simplification: by working in the log-Euclidean framework, all the Riemannian geometry is absorbed into the feature extraction step, and the invariance training proceeds in a flat space.

### 14.5.5 Evaluation: DRI Before and After Invariance Training

The diagnostic power of combining gradient reversal (prescriptive) with the DRI (diagnostic) is substantial. After invariance training, we re-run the DRI using the same acoustic transform suite:

```python
from eris_ketos.acoustic_transforms import make_acoustic_transform_suite
from eris_ketos.decoder_robustness import DecoderRobustnessIndex

transforms = make_acoustic_transform_suite()
dri = DecoderRobustnessIndex(transforms)

# Measure robustness BEFORE invariance training
result_before = dri.measure(baseline_decoder, signals, sr=32000)

# Measure robustness AFTER invariance training
result_after = dri.measure(invariant_decoder, signals, sr=32000)

# Compare per-transform sensitivity
for name in result_before.per_transform:
    before = result_before.per_transform[name]
    after = result_after.per_transform[name]
    reduction = (before - after) / max(before, 1e-10) * 100
    print(f"{name:20s}  {before:.3f} -> {after:.3f}  ({reduction:+.1f}%)")
```

The expected pattern: transforms that correspond to the recording-condition nuisance variable (amplitude scaling, additive noise, spectral masking) should show large DRI reductions after invariance training. Transforms that correspond to biological signal changes (time stretching, Doppler shift) should show minimal change, because the encoder still needs to encode temporal structure.

If a recording-condition transform still shows high DRI after invariance training, this is diagnostic: either the domain head was too weak to detect that nuisance factor, or the factor is entangled with the biological signal in a way that gradient reversal at the chosen $\lambda$ cannot disentangle. In either case, the DRI identifies exactly *which* nuisance factors remain problematic, guiding targeted improvements to the architecture or training procedure.

---

## 14.6 Connection to Adversarial Robustness (Chapter 9)

### 14.6.1 Two Sides of the Same Coin

Chapter 9's adversarial robustness testing and this chapter's gradient reversal training are dual perspectives on the same geometric problem. Both concern the relationship between the encoder's latent space and a set of transformations applied to the input:

| Aspect | Ch 9: Adversarial Testing | Ch 14: Gradient Reversal |
|---|---|---|
| **Goal** | Diagnose sensitivity | Enforce invariance |
| **When** | After training | During training |
| **Mechanism** | Apply transforms, measure output change | Reverse gradients from nuisance predictor |
| **Output** | DRI score, sensitivity profile | Invariant encoder |
| **Geometry** | Measures distances in output space under perturbation | Projects representation onto complement of nuisance subspace |

The connection is more than analogical. The DRI's per-transform sensitivity profile (Section 9.4 of Chapter 9) provides exactly the information needed to configure gradient reversal training: transforms with high DRI scores identify the nuisance dimensions that the encoder has memorized, and these dimensions define the nuisance variable $s$ for the domain discriminator.

### 14.6.2 The Feedback Loop

The ideal workflow composes both methods:

1. **Baseline training.** Train the encoder with the standard task loss only.
2. **Diagnostic fuzzing.** Apply the DRI to identify which nuisance factors the encoder is sensitive to. This corresponds to the sensitivity profile from `eris_ketos.decoder_robustness`:

```python
profile = dri.sensitivity_profile(decoder, signals, sr=32000)
# profile: {"amplitude_scale": 0.02, "additive_noise": 0.31,
#            "pink_noise": 0.28, "spectral_mask": 0.45, ...}
```

3. **Invariance training.** Attach gradient reversal with domain labels corresponding to the high-sensitivity transforms. Train to invariance.
4. **Validation fuzzing.** Re-run the DRI to confirm that sensitivity has decreased. Check that task accuracy has not degraded excessively.
5. **Iterate.** If residual sensitivity remains, adjust $\lambda$, strengthen the domain head, or add additional nuisance labels.

This loop is the invariance analogue of the "fuzz-diagnose-fix-verify" cycle in software security. The structural fuzzing framework provides the diagnostic infrastructure; gradient reversal provides the fix.

### 14.6.3 The Adversarial Threshold Connection

Chapter 9 introduced adversarial threshold search: binary search for the minimal transform intensity that flips the decoder's output. The implementation in `eris_ketos.decoder_robustness` finds the exact tipping point:

```python
threshold = dri.find_adversarial_threshold(
    decoder, signal, sr, transform, tolerance=0.01
)
```

Gradient reversal training should *raise* these thresholds for nuisance transforms. An encoder invariant to additive noise should require a much higher noise intensity to flip its output than a non-invariant encoder. Tracking adversarial thresholds before and after invariance training provides a precise, per-transform measure of the improvement:

$$\Delta_{\text{threshold}}(t) = \tau_{\text{after}}(t) - \tau_{\text{before}}(t)$$

A positive $\Delta_{\text{threshold}}$ for nuisance transform $t$ indicates successful invariance training along that dimension. A near-zero $\Delta_{\text{threshold}}$ indicates failure. This metric is complementary to the DRI: the DRI measures average sensitivity, while the adversarial threshold measures worst-case robustness.

---

## 14.7 Practical Considerations

### 14.7.1 Choosing the Nuisance Variable

The choice of nuisance variable is a modeling decision with geometric consequences. Define it too narrowly (e.g., invariance to amplitude scaling only), and the encoder remains sensitive to other recording conditions. Define it too broadly (e.g., invariance to "everything about the recording"), and the nuisance subspace may consume so much of the latent space that task performance collapses.

The right approach is guided by the DRI's sensitivity profile. Start with the highest-sensitivity transforms and add nuisance dimensions incrementally, checking task accuracy at each step. The `is_invariant` flag on the `AcousticTransform` dataclass provides a principled starting taxonomy:

```python
from eris_ketos.acoustic_transforms import make_acoustic_transform_suite

transforms = make_acoustic_transform_suite()
invariant_transforms = [t for t in transforms if t.is_invariant]
# ['amplitude_scale', 'time_shift', 'additive_noise', 'pink_noise']
```

These are the transforms that a correct decoder *should* be invariant to. They define the initial nuisance variable. If the DRI reveals additional sensitivities (e.g., to `multipath_echo` or `spectral_mask`), those can be added to the nuisance set in subsequent training rounds.

### 14.7.2 Domain Head Capacity

The domain discriminator must be strong enough to detect nuisance information when it is present, but not so strong that the adversarial game becomes unstable. In practice, a two-to-three-layer MLP with hidden dimensions roughly half the encoder's latent dimension works well. If the domain head is too weak, it will appear to converge (high domain accuracy plateau) before gradient reversal training has a chance to enforce invariance. If it is too strong, the minimax game oscillates without converging.

A useful diagnostic: if domain accuracy oscillates wildly during training rather than smoothly decreasing, the domain head is too powerful relative to $\lambda$. Reduce the domain head's capacity or decrease $\max\_\lambda$.

### 14.7.3 Multi-Source Invariance

In many practical settings, there are multiple nuisance variables: recording device, ocean basin, season, depth. These can be handled by either:

1. **Multiple domain heads**, each with its own GRL and nuisance label:

```python
class MultiSourceDANN(nn.Module):
    """DANN with multiple independent domain heads."""

    def __init__(
        self,
        encoder: nn.Module,
        task_head: nn.Module,
        domain_heads: dict[str, nn.Module],
        lambdas: dict[str, float],
    ) -> None:
        super().__init__()
        self.encoder = encoder
        self.task_head = task_head
        self.domain_heads = nn.ModuleDict(domain_heads)
        self.grls = nn.ModuleDict(
            {k: GradientReversalLayer(v) for k, v in lambdas.items()}
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, dict]:
        z = self.encoder(x)
        task_logits = self.task_head(z)
        domain_logits = {
            name: head(self.grls[name](z))
            for name, head in self.domain_heads.items()
        }
        return task_logits, domain_logits
```

2. **A single domain head** with a concatenated nuisance label. This is simpler but cannot assign different $\lambda$ values to different nuisance factors.

The multi-head approach is preferable when the nuisance factors have different scales of importance. For cetacean bioacoustics, recording-device invariance might warrant a high $\lambda$ (the model should never depend on the hydrophone), while seasonal invariance might warrant a lower $\lambda$ (some seasonal variation in vocal behavior is genuine and should be preserved).

---

## 14.8 Theoretical Guarantees and Limitations

### 14.8.1 The Ben-David Bound

The theoretical foundation for gradient reversal in domain adaptation is the Ben-David et al. (2010) bound on target-domain error:

$$\epsilon_T(h) \leq \epsilon_S(h) + d_{\mathcal{H}\Delta\mathcal{H}}(S, T) + C$$

where $\epsilon_S(h)$ is the source-domain error, $d_{\mathcal{H}\Delta\mathcal{H}}(S, T)$ is the $\mathcal{H}\Delta\mathcal{H}$-divergence between source and target domains, and $C$ is a constant reflecting the best achievable error on both domains simultaneously.

Gradient reversal minimizes the middle term: by forcing the encoder to produce domain-invariant representations, it drives $d_{\mathcal{H}\Delta\mathcal{H}}(S, T)$ toward zero. But the bound also contains $C$, which reflects the fundamental tradeoff: if the optimal classifier differs between domains, no invariant representation can achieve low error on both. This is the geometric statement that the task and nuisance subspaces overlap.

### 14.8.2 When Gradient Reversal Fails

Gradient reversal can fail in three ways:

1. **The nuisance and task subspaces coincide.** If the only features predictive of the task are also predictive of the nuisance variable, enforcing invariance destroys task-relevant information. This is the $C > 0$ case in the Ben-David bound.

2. **The domain discriminator is too weak.** If $h_\psi$ cannot detect nuisance information in $\mathbf{z}$, the reversed gradient is noise, and the encoder learns nothing about invariance. This is a practical failure, not a theoretical one.

3. **The minimax game does not converge.** Like all adversarial training, gradient reversal can exhibit mode collapse, oscillation, or divergence. The lambda schedule mitigates this but does not eliminate it.

In all three cases, the DRI provides an objective diagnostic. If the DRI for nuisance transforms does not decrease after gradient reversal training, one of these failures has occurred, and the per-transform breakdown indicates which nuisance factors remain problematic.

---

## 14.9 Worked Example: Five-Hydrophone Experiment

To make the preceding theory concrete, consider a controlled experiment with coda recordings from five different hydrophone deployments. The task is to classify coda types (23 classes). The nuisance variable is the hydrophone deployment (5 categories).

```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# Simulated data: 2000 spectrograms from 5 hydrophones
n_samples = 2000
n_mels = 128
n_frames = 64
n_coda_types = 23
n_hydrophones = 5

torch.manual_seed(42)
spectrograms = torch.randn(n_samples, 1, n_mels, n_frames)
coda_labels = torch.randint(0, n_coda_types, (n_samples,))
hydrophone_labels = torch.randint(0, n_hydrophones, (n_samples,))

dataset = TensorDataset(spectrograms, coda_labels, hydrophone_labels)
loader = DataLoader(dataset, batch_size=64, shuffle=True)

# Build and train the invariant classifier
model = build_invariant_coda_classifier(
    n_mels=n_mels,
    latent_dim=128,
    n_coda_types=n_coda_types,
    n_conditions=n_hydrophones,
    max_lambda=0.5,
)

optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
task_criterion = nn.CrossEntropyLoss()
domain_criterion = nn.CrossEntropyLoss()

history = train_dann(
    model=model,
    train_loader=loader,
    optimizer=optimizer,
    task_criterion=task_criterion,
    domain_criterion=domain_criterion,
    total_epochs=50,
    gamma=10.0,
    max_lambda=0.5,
)

# Verify: domain accuracy should approach chance (1/5 = 20%)
print(f"Final domain accuracy: {history['domain_accuracy'][-1]:.1%}")
print(f"Chance level: {1/n_hydrophones:.1%}")
```

At convergence, the domain accuracy should approach 20% (chance level for 5 hydrophones), indicating that the encoder's latent representation no longer contains hydrophone-discriminative information. The task accuracy may decrease slightly relative to a non-invariant baseline---this is the price of invariance, and the DRI confirms whether the price was worth paying.

---

## 14.10 Summary

The gradient reversal layer is a minimal intervention---five lines of autograd logic---with a maximal geometric effect: it projects the encoder's latent representation onto the orthogonal complement of the nuisance subspace, producing representations that are invariant to specified surface features by construction.

The chapter developed five interconnected ideas:

1. **The invariance problem.** Encoders trained with standard losses memorize surface features (recording conditions, domain identity, equipment characteristics) alongside the signal of interest. This produces models that are accurate in-distribution but fragile under domain shift.

2. **The gradient reversal layer.** A domain discriminator predicts the nuisance variable from the latent representation. The GRL negates the gradient flowing from the discriminator back through the encoder, forcing the encoder to make the nuisance variable unpredictable. The combined system solves a minimax game.

3. **The geometric interpretation.** Gradient reversal decomposes the latent space into a task subspace and a nuisance subspace, then projects onto the orthogonal complement of the nuisance subspace. On non-Euclidean feature spaces (such as the SPD manifold for spectral covariance), the projection operates in the tangent space via the log-Euclidean map.

4. **The cetacean bioacoustics application.** Recording conditions (hydrophone response, ambient noise, ocean reverberation) contaminate spectral features. Gradient reversal forces the encoder to be invariant to these conditions while preserving biological signal---coda type, rhythmic pattern, spectral content.

5. **The feedback loop with adversarial testing.** The DRI from Chapter 9 diagnoses which nuisance factors the encoder is sensitive to; gradient reversal eliminates those sensitivities; the DRI validates the result. The two methods compose into a "diagnose-treat-verify" pipeline.

---

## 14.11 Forward Connection: Chapter 15

The invariance enforced by gradient reversal is *learned*: the encoder discovers which features to discard through the adversarial training process. Chapter 15 introduces a complementary approach based on **group-theoretic augmentation**, where invariances are *specified* rather than learned. If you know that coda classification should be invariant to time shifts, amplitude scaling, and circular permutations of the click sequence, you can encode these invariances directly into the architecture or the training data via group actions---transformations that form a mathematical group under composition.

The two approaches---learned invariance (gradient reversal) and specified invariance (group augmentation)---address different parts of the invariance spectrum. For nuisance variables that can be precisely characterized as group actions (rotations, translations, permutations), group-theoretic methods are more efficient and provide exact invariance guarantees. For nuisance variables that cannot be characterized as group actions (recording conditions, domain identity), gradient reversal is the appropriate tool. Chapter 15 develops the group-theoretic side and shows how the two approaches combine.
