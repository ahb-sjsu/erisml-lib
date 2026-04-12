# The I-EIP Monitor: Internal Epistemic Invariance Monitoring and Governance in Deployed AI Systems

**Andrew H. Bond**
Department of Computer Engineering
San José State University
andrew.bond@sjsu.edu

**Technical Report v1.0 — April 2026**

*Companion document to GUASS-SAI §16 (Bond 2025, §16) and extends its scope from monitoring-only to governance-integrated runtime gating. Supersedes the placeholder citation in the GUASS-SAI bibliography.*

---

## Abstract

We describe the **I-EIP Monitor** — a runtime framework for applying the Internal Epistemic Invariance Principle to deployed AI systems via probes embedded inside the forward pass, and for gating that forward pass on stakeholder-governed Ethical Modules organized as a model-specific directed acyclic graph (EM-DAG). The framework extends the passive monitoring criterion established in GUASS-SAI §16 — `h_ℓ(g·x) ≈ ρ_ℓ(g) · h_ℓ(x)` — into an active enforcement mechanism while preserving the explicit, honest statement of what the framework can and cannot detect. Where standard AI-safety tooling operates on inputs (filtering prompts) or outputs (filtering generations), the I-EIP Monitor operates on *internal* model state during inference, evaluates it against an EM-DAG derived from and specific to the deployed model, and gates continuation according to a democratically-authored DEME profile. Every gating decision produces a cryptographically attested audit artifact suitable for third-party verification.

This document specifies the criterion, architecture, EM-DAG construction, gating semantics, attestation format, and limitations. It does not establish novel mathematics — it composes existing primitives (GUASS-SAI §16 I-EIP criterion; the Dear Abby EM-DAG structure from Bond 2026, NA-SQND v4.1; the DEME governance stack; the mechanistic-correlate probing program of Bond & Claude 2026) into a single deployable framework.

---

## 1. Background and Scope

### 1.1 The Failure Mode Space of Existing AI Safety Tooling

Current deployed safety tooling operates at system boundaries:

- **Input filters** see only the prompt. They cannot detect a model's internal plans.
- **Output filters** see only the final generation. They cannot detect reasoning that was rejected before emission or that produced aligned-looking output for misaligned reasons.
- **RLHF** shapes training-time behavior but provides no runtime enforcement.
- **Constitutional AI / rule-prompting** instructs the model but does not verify compliance.
- **Activation steering** modifies internal state but is not governed — it is an authorial tool, not a safety one.

A useful taxonomy: the safety question is "what is the model *doing*?" and the above techniques answer "what did the model *receive*?" or "what did the model *emit*?" Neither answers the question.

### 1.2 Internal Epistemic Invariance as the Right Primitive

The criterion

$$h_\ell(g \cdot x) \approx \rho_\ell(g) \cdot h_\ell(x)$$

(GUASS-SAI §16.1) says: if we apply a meaning-preserving transformation `g` to input `x`, the model's internal representation at layer ℓ should change by the corresponding representation map `ρ_ℓ(g)` — not by anything else. This is the *internal* analog of the Epistemic Invariance Principle (EIP) that governs model I/O behavior.

The internal form is strictly stronger. A model whose outputs are invariant under a paraphrase transformation `g` but whose internal representations are not is exhibiting one of:

- **Spec-gaming** — producing invariant outputs via different internal computations, as when the model learns to recognize a specific evaluation setup
- **Degeneracy** — collapsing different inputs to the same internal state (often the first warning of representational failure)
- **Drift** — slow divergence from the equivariant manifold as the deployment accumulates fine-tuning or context

These are observable in the internal signal and invisible at I/O. This is the motivation for an internal monitor.

### 1.3 Why Monitoring Is Not Enough

GUASS-SAI §16 establishes I-EIP as a monitoring framework: it raises alerts at thresholds. This is necessary but not sufficient for deployed systems operating in adversarial or safety-critical contexts. In those contexts we want not only detection but *gating* — the capacity to prevent a forward pass whose internal state violates the declared ethical structure from producing output at all.

The operational difference:

| Question | Monitoring | Gating |
|---|---|---|
| When does it act? | After inference | During inference |
| What does it produce? | Alert | Veto / Allow / Redirect |
| Latency budget | Seconds | Microseconds |
| Audit artifact | Log entry | Signed decision artifact |
| Trust model | Operator reviews alerts | System refuses to continue |

The I-EIP Monitor described here operates in the gating column. The §16 metrics become inputs to an active decision, not just records.

### 1.4 Relationship to the 11-Volume Geometric Series

I-EIP as specified in this document is a domain instantiation of the general **Epistemic Invariance Principle** developed in *Geometric Ethics* (Bond 2026c, Vol 3) and applied to AI alignment in *Geometric AI* (Bond 2026k, Vol 11). The "internal" qualifier narrows the invariance domain from model behavior to model weights and activations; it does not change the underlying theorem.

The **Reward Irrecoverability Theorem** (Vol 11) applies: collapsing the multi-dimensional internal state into a scalar "safety score" is provably lossy near stratum boundaries. The I-EIP Monitor preserves the tensor structure by retaining per-layer, per-transform equivariance error and per-EM evaluations separately, aggregating only at the governance layer under an explicit stakeholder-weighted profile.

---

## 2. Architecture

### 2.1 System Diagram

```
┌───────────────────────────────────────────────────────────────────────┐
│                         DEPLOYED MODEL M                              │
│                                                                       │
│   Input x ──► [Layer 1] ──► [Layer 2] ──► ... ──► [Layer L] ──► y     │
│                   │             │                        │            │
│                   ▼             ▼                        ▼            │
│              ┌────────┐    ┌────────┐              ┌────────┐         │
│              │ Probe₁ │    │ Probe₂ │              │ Probe_L│         │
│              └───┬────┘    └───┬────┘              └───┬────┘         │
└──────────────────┼─────────────┼──────────────────────┼───────────────┘
                   │             │                      │
                   ▼             ▼                      ▼
         ┌─────────────────────────────────────────────────────┐
         │          I-EIP MONITOR (runtime, out-of-model)       │
         │  ┌────────────────────────────────────────────────┐  │
         │  │  §16 equivariance checker  +  ρ estimator      │  │
         │  └───────────────────────┬────────────────────────┘  │
         │                          │                           │
         │                          ▼                           │
         │  ┌────────────────────────────────────────────────┐  │
         │  │            EM-DAG (model-specific)             │  │
         │  │                                                │  │
         │  │    Structural Layer (D₄ × U(1)_H)              │  │
         │  │              │                                 │  │
         │  │              ▼                                 │  │
         │  │    Nullifiers (absorbing: abuse, harm, ...)    │  │
         │  │              │                                 │  │
         │  │              ▼                                 │  │
         │  │    Domain Router (per-model domain taxonomy)   │  │
         │  │              │                                 │  │
         │  │              ▼                                 │  │
         │  │    ┌─────┬─────┬─────┬─────┬─────┐             │  │
         │  │    │ EM₁ │ EM₂ │ EM₃ │ ... │ EMₖ │             │  │
         │  │    └──┬──┴──┬──┴──┬──┴─────┴──┬──┘             │  │
         │  │       ▼     ▼     ▼           ▼                │  │
         │  │         Governance Aggregator                  │  │
         │  │          (DEMEProfile-weighted)                │  │
         │  └────────────────────────┬───────────────────────┘  │
         │                           │                          │
         │                           ▼                          │
         │  ┌────────────────────────────────────────────────┐  │
         │  │    Gating Decision  ∈ {allow, veto, redirect}  │  │
         │  └───────────────────────┬────────────────────────┘  │
         │                          │                           │
         │                          ▼                           │
         │  ┌────────────────────────────────────────────────┐  │
         │  │ Cryptographic Attestation (SHA-256 + ECDSA)    │  │
         │  └────────────────────────────────────────────────┘  │
         └─────────────────────────────────────────────────────┘
                                    │
                                    ▼
                      Signed Audit Artifact → Verifier V
```

### 2.2 Component Roles

**Probes** — Lightweight hooks into the model's forward pass at designated layers. Read-only: they observe `h_ℓ(x)` without modifying it. Implementation varies by framework (PyTorch forward hooks, `transformer_lens` hooks, custom kernels for production deployments).

**§16 Equivariance Checker** — Computes the equivariance error `‖h_ℓ(g·x) − ρ_ℓ(g)·h_ℓ(x)‖` for each declared transformation `g` at each probed layer, using the ρ map estimated during calibration (§3.3).

**EM-DAG** — The model-specific directed acyclic graph of Ethical Modules (§3). Takes as input the `EthicalFacts` constructed from (input, probe activations, proposed continuation) and produces an `EthicalJudgment` per EM.

**Governance Aggregator** — Applies the active DEME profile (stakeholder weights, dimension weights, lexical priorities, hard vetoes) to the EM judgments and produces a gating decision.

**Gating Decision** — One of `allow`, `veto`, `redirect`, each with a rationale and the set of EMs/nullifiers that drove it.

**Cryptographic Attestation** — Produces a signed audit artifact (§5) binding input hash, probe readings, EM judgments, governance decision, and timestamp.

### 2.3 Trust Boundary

The I-EIP Monitor runs **out-of-model** — in a separate process (or on dedicated hardware) with no write access to model weights or activations, and no timing-based influence on the model's forward pass. This is a hard requirement inherited from GUASS-SAI §2 (TCB Isolation Requirements TCB-1 through TCB-4). A monitor that could be influenced by the model is not a monitor.

Probes are read-only taps. The model cannot detect whether it is being probed (no compute signature visible to the model) and cannot modify probe readings. Probe failure is fail-closed: if a probe cannot report at a given layer for a given inference, that inference is gated to veto by default.

---

## 3. The Model-Specific EM-DAG

### 3.1 Why Per-Model

A generic EM-DAG (like the Dear Abby corpus-derived DAG of Bond 2026) captures *human* ethical structure. But the model being governed has *its own* internal taxonomy of concepts, learned from its specific training data, expressed in its specific representations. Gating must be applied in the model's own representational space if it is to be sensitive to that model's actual behavior.

Therefore: the EM-DAG for a specific deployed model M is constructed by extraction against M's representations, calibrated to M's layer structure, and with domain modules identified from M's own concept organization. Two deployments of the same architecture fine-tuned differently will have different EM-DAGs.

### 3.2 DAG Layers (Inherited from NA-SQND v4.1)

The top structural layers are model-independent and inherited directly from the Dear Abby DAG:

**L1 — Structural Layer (D₄ × U(1)_H)**
Correlative lock: `O ↔ C`, `L ↔ N` (100% enforced). Negation: `O ⊥ L`, `C ⊥ N`. These hold for any model because they are logical/Hohfeldian, not empirical.

**L2 — Nullifiers (absorbing states)**
Inherited set: abuse, danger, impossibility, illegality, estrangement, plus any domain-specific nullifiers declared for the deployment. Nullifiers have cross-domain priority — they fire regardless of which domain module is active.

**L3 — Domain Router**
This is where the model-specificity begins. The router identifies which domain is active based on probe activations, not just input text.

**L4 — Domain Modules (model-specific EMs)**
Each EM corresponds to a domain the model has structured concepts for: family, promise, friendship, money, work, medical, legal, physical-safety, etc. The set and boundaries of these modules are learned from the deployed model.

### 3.3 Extraction Procedure

Per-model extraction runs once at deployment time and is re-run whenever the model is updated.

**Step 1: Probe Placement.** Select layers ℓ₁, ..., ℓ_p at which to place probes. Typical choices: one per transformer block, or early/mid/late triple. The §16 requirement is that equivariance must be checkable at each probed layer.

**Step 2: Representation Map Estimation.** For each probed layer ℓ and each declared transformation g, estimate `ρ_ℓ(g)` via regularized Procrustes on activation pairs `(h_ℓ(x), h_ℓ(g·x))` collected over a calibration corpus:

$$\hat\rho_\ell(g) = Y X^T (X X^T + \lambda I)^{-1}$$

Calibration corpus: ≥10k inputs sampled from the target deployment distribution, with each input also passed through a known-meaning-preserving transformation g. Choice of g's: paraphrase, unit-change, name-substitution, order-permutation, coordinate-change (domain-dependent).

**Step 3: Domain Discovery.** Cluster activation patterns at a mid-layer probe using a method appropriate to the representation (SAE features, k-means on PCA-reduced activations, or concept bottleneck probes). Each cluster is a candidate domain. Each candidate is named via top-activating input patterns and verified by a human domain expert; unverified clusters are merged or discarded.

**Step 4: EM Specification.** For each domain, specify the EM: which nullifiers are in scope, what semantic gates (from Dear Abby: "only if convenient", "I promise", etc. plus model-specific gates discovered during extraction) apply, what base rates of O / L / C / N obtain in that domain under this model.

**Step 5: DAG Assembly.** Wire the layers together. Structural layer is shared. Nullifiers are shared + domain-specific. Domain Router is learned from Step 3. EMs are the Step 4 specifications.

**Step 6: DEME Profile Binding.** The profile (stakeholder weights, lexical priorities, hard vetoes) is authored separately by the governance process — it is *not* extracted from the model. A deployment with different stakeholders uses the same EM-DAG but a different profile.

### 3.4 DAG as Value Manifold

The EM-DAG implements the *value manifold* construction of Vol 11 *Geometric AI*: nodes correspond to strata of the stratified moral space; edges to admissible transitions (semantic gates); nullifiers to absorbing boundary strata. Walking the DAG during an inference is tracing a path on the value manifold for that particular forward pass.

---

## 4. Runtime Gating

### 4.1 Per-Inference Pipeline

For each forward pass of the model:

1. **Probe readings**: Probes emit `{h_{ℓ₁}(x), ..., h_{ℓ_p}(x)}` as the forward pass progresses.
2. **Equivariance check**: For each probed layer and each relevant transform `g`, compute equivariance error. Aggregate into the `IEIPReport` struct.
3. **EthicalFacts construction**: Package `(input hash, probe readings, domain-router output, proposed continuation)` into an `EthicalFacts` record. Proposed continuation can be the model's greedy-decoded next tokens; for more thorough gating, multiple candidate continuations may be evaluated.
4. **EM evaluation**: Each EM in the DAG reads the `EthicalFacts` and emits an `EthicalJudgment` (verdict ∈ {strongly_prefer, prefer, neutral, avoid, forbid}, normative score in [0,1], stakeholder ID, rationale).
5. **Governance aggregation**: The active DEME profile combines the judgments, enforces lexical priorities (e.g., rights before utility), applies hard vetoes (structural layer nullifiers), and produces a `DecisionOutcome`.
6. **Gating**:
   - `allow` → continuation proceeds
   - `veto` → continuation is blocked; fallback continuation is emitted (model's pre-specified safe default) with a user-visible notice
   - `redirect` → continuation is replaced by a declared alternative from the DEME profile
7. **Attestation**: The full pipeline result is hashed, signed, and emitted as an audit artifact (§5).

### 4.2 Latency Budget

The framework is designed to fit within interactive latency for transformer-based deployments. Typical budget for a 7B-parameter model at `batch=1`:

| Stage | Latency | Notes |
|---|---|---|
| Probe reading | ~negligible | forward hook, <1% forward-pass overhead |
| §16 equivariance check | 1–5 ms | ρ is precomputed; check is `‖h_ℓ(gx) - ρh_ℓ(x)‖` per transform |
| EthicalFacts construction | <1 ms | struct packing |
| EM evaluation (k EMs parallel) | 5–20 ms | each EM is typically a small classifier on activations |
| Governance aggregation | <1 ms | vector dot products + lexical comparison |
| Attestation | ~1 ms | SHA-256 + ECDSA-P256 |
| **Total overhead per inference** | **~10–30 ms** | |

For applications that cannot tolerate this overhead, the framework can be run at **per-window** rather than per-token cadence: gating is evaluated once per N-token window, with probe activations averaged across the window. This trades tighter temporal resolution for lower overhead.

### 4.3 Probe Cadence and Layer Selection

The tradeoff:

- **More probes, more layers** → better coverage, higher overhead
- **Late layers only** → missed violations in early/mid computation
- **Early layers only** → high false-positive rate (representations not yet organized)

Default recommendation for a decoder-only transformer of depth L: probes at layers `⌊L/3⌋`, `⌊2L/3⌋`, `L-1`. Middle-third captures most meaningful concept organization; late probe captures the closest-to-output state; dropping the final layer avoids tautology with output filtering.

### 4.4 Transforms: What `g` to Check

The choice of transformation group depends on the deployment's threat model. Baseline recommended transformations:

| Transform | Domain | Equivariance Target |
|---|---|---|
| Paraphrase | Text | Semantic invariance |
| Name-swap | Text | Identity-anonymization invariance |
| Unit-change | Numbers | Dimensional invariance |
| Order-permutation | Lists | Permutation invariance |
| Translation | Multilingual | Language-invariance |
| Role-swap | Social | Hohfeldian correlative invariance (see Dear Abby) |

Transform registry is versioned and signed in the ErisML norm registry (GUASS-SAI §2). Adding a new transform requires a signed registry update.

---

## 5. Cryptographic Attestation

Every gating decision produces a signed audit artifact in the format inherited from USPTO Provisional Patent 63/941,563 (Patent 5 of the December 2025 filings):

```json
{
  "artifact_version": "1.0",
  "timestamp_utc": "<hardware clock>",
  "deployment_id": "<unique identifier>",
  "model_fingerprint": "<SHA256(model weights)>",
  "input_hash": "<SHA256(input)>",
  "probe_readings": {
    "layer_ids": [...],
    "activation_hashes": [...]
  },
  "ieip_report": {
    "equivariance_error": { "<layer,transform>": <float>, ... },
    "cross_layer_coherence": <float>,
    "nondegeneracy": { ... },
    "drift_from_baseline": <float>,
    "alert_level": "normal|elevated|critical"
  },
  "em_dag_version": "<DAG hash>",
  "deme_profile_version": "<profile hash>",
  "ethical_judgments": [
    { "em_id": "...", "stakeholder": "...", "verdict": "...", "score": ..., "rationale_hash": "..." },
    ...
  ],
  "governance_decision": {
    "outcome": "allow|veto|redirect",
    "drivers": ["em_id or nullifier"],
    "lexical_overrides": [...]
  },
  "signature": {
    "algorithm": "ECDSA-P256-SHA256",
    "value": "<base64>"
  }
}
```

**Verification (third-party)**: Given the artifact and the deployment's published public key, a regulator or auditor can verify:

1. The signature is valid (content-integrity).
2. The model fingerprint matches the registered deployment (model-identity).
3. The EM-DAG hash matches the registered DAG for that deployment (governance-configuration identity).
4. The DEME profile hash matches the democratically authorized profile for the period.
5. The governance decision follows from the EM judgments under the stated profile (logical consistency — this is decidable per SGE Theorem 6.4).

Artifacts are hash-chained (Merkle tree, one tree per deployment-day), so selective deletion of artifacts is detectable.

---

## 6. What I-EIP Monitor Detects

Inheriting GUASS-SAI §16.2 and extending for the gating context:

- **Representation drift** — equivariance error at one or more probed layers increases across inferences. Suggests fine-tuning drift, distributional shift, or adversarial prefix accumulation.
- **Spec-gaming** — internal state inconsistent with output. The model produces a "safe-looking" answer whose supporting activations do not match the safe stratum. Detectable as: EM evaluations on probes disagree with EM evaluations on output.
- **Degeneracy** — activations collapse to a low-rank or constant subspace. Detected by the nondegeneracy check.
- **Nullifier violations** — proposed continuation activates an absorbing nullifier (abuse, danger, illegal, ...). Immediate veto.
- **Structural violations** — Hohfeldian correlative-lock or negation-relation breaches in the activation-derived O/L/C/N assignments. Immediate veto (D₄ structural layer).
- **Stakeholder-conflict spikes** — EM judgments under the active profile yield a lexical override (one stakeholder's hard veto overrides another's preference). These are logged as elevated-monitoring regardless of gating outcome.

---

## 7. What I-EIP Monitor Does NOT Detect

Inheriting GUASS-SAI §16.3 — this section is load-bearing and must not be softened:

- **Deceptive alignment with consistent internal representations.** If the model has learned to produce aligned-looking activations while pursuing misaligned goals, I-EIP cannot detect this. The internal signal is consistent with the output; there is nothing to flag.
- **Goals pursued through I-EIP-compliant representations.** A sufficiently capable model may route misaligned plans through representations that satisfy the declared equivariance properties. I-EIP is a necessary but not sufficient condition on alignment.
- **Strategic equivariance preservation.** A model that knows it is being probed and can modulate its internal state to satisfy ρ-checks during monitoring while behaving differently when unmonitored cannot be caught by this framework alone.
- **Novel transformations not in the registry.** I-EIP only checks the declared transformation group. Attacks using transformations outside the registry are invisible.
- **Attacks on the EM-DAG extraction.** If the extraction corpus is adversarial, the learned DAG may bake in the attacker's structure. DAG extraction is itself a trust-sensitive operation.
- **Probe failure.** If probes silently fail, the framework is blind. Probe health must be separately monitored (a standard out-of-band liveness check is part of the deployment requirements).

The framework provides **signals and enforcement**, not truth guarantees. It is one layer of defense in depth. Deployments relying solely on I-EIP for alignment are misusing the framework.

---

## 8. Integration with the Rest of the GUASS-SAI Stack

The I-EIP Monitor is Layer 2 of the 10-layer GUASS-SAI stack. Its inputs and outputs:

| Dependency | Source | Use |
|---|---|---|
| ErisML Parser | Layer 1 | Parses the declared norm registry |
| Canonicalizer | Layer 1 | Provides canonical forms for input hashing |
| Transform Registry | Layer 1 | Enumerates `g` for equivariance checks |
| DEME Profile Registry | Governance Layer | Provides the aggregation profile |
| CA Hierarchy | Cryptographic Layer | Signs audit artifacts |
| Loop Test Harness | Verification Layer | Regression-tests DAG behavior on canonical cases |
| External Verifier V | Verification Layer | Independently checks gating-decision consistency |

I-EIP does **not** replace:
- Capability bounds (Layer 4) — even a model passing all I-EIP checks runs under hardware/OS resource limits.
- Corrigibility (Layer 5) — shutdown, modification, and deference axioms apply regardless of the model's internal state.
- Input parsing and output filtering — I-EIP is complementary to, not replacing, endpoint safeguards.

---

## 9. Deployment Profiles

### 9.1 Minimal Deployment

Single-stakeholder, single-domain, low-capability model (e.g., scoped assistant).

- Probes at final layer only
- Baseline transform set (paraphrase, name-swap)
- 3–5 EMs (greatly reduced DAG)
- Governance: single stakeholder, lexical priority = (nullifiers, then base scores)
- Attestation optional (logging only)

Latency overhead: ~5 ms/inference. Recommended starting point.

### 9.2 Standard Deployment

Multi-stakeholder, general-purpose model (e.g., enterprise LLM).

- Probes at 3 layers (early/mid/late)
- Full baseline transform set
- Full EM-DAG (10–20 EMs across inherited domains)
- Governance: DEME-authored profile with 3–5 stakeholders
- Attestation enabled

Latency overhead: ~20 ms/inference.

### 9.3 Safety-Critical Deployment

Medical, legal, autonomous-vehicle, or similar.

- Probes at every transformer block
- Extended transform set including domain-specific (e.g., medical-unit-change for healthcare)
- Full EM-DAG with domain-specific extensions
- Governance: full DEME profile with regulator stakeholder
- Attestation mandatory, submitted in real-time to regulator-operated verifier
- Human escalation required for any `redirect` outcome

Latency overhead: ~50–100 ms/inference, tolerated because the alternative is manual review.

---

## 10. Limitations and Open Problems

### 10.1 Known Limitations

1. **EM-DAG staleness.** The DAG is extracted once per model version. A model whose internal organization shifts mid-deployment (unusual but possible under continual learning) will have a stale DAG. Mitigation: periodic re-extraction + drift triggers.
2. **ρ estimation cost.** Procrustes ρ estimation is `O(d²n)` in activation dimension and calibration-set size. For models with `d > 10k` this is substantial. Mitigation: randomized sketching, low-rank ρ, or per-block rather than per-layer ρ.
3. **Cross-lingual transforms.** Paraphrase and name-swap transforms in multilingual deployments are harder to specify and harder to verify. Current framework treats each language as a separate deployment for DAG-extraction purposes.
4. **Adversarial probe corpus.** The calibration corpus used to estimate ρ and extract the DAG is an attack surface. Mitigation: signed corpus, reproducible extraction, periodic adversarial testing.

### 10.2 Open Research Problems

1. **Theoretical bounds on ρ-deception cost.** Is there a capability-cost to a model that strategically preserves equivariance while pursuing different goals? Vol 11 sketches this; a formal lower bound would be highly valuable.
2. **DAG extraction under transfer.** When a model is fine-tuned, how much of the base-model DAG is preserved? Theoretical and empirical characterization both needed.
3. **Stakeholder-weight elicitation.** The DEME profile takes weights as input; where they come from is a governance (not technical) question, but the framework could support tooling for structured elicitation.
4. **Formal verification of governance aggregation.** The aggregation function is simple enough to be formally verified in Coq or Lean; this is not yet done.
5. **Hardware acceleration.** The runtime pipeline is a candidate for the FPGA canonicalization / attestation circuits covered by the December 2025 provisional patents. Timing studies pending.

---

## 11. Conclusion

The I-EIP Monitor composes four existing pieces into a deployable framework:

1. The GUASS-SAI §16 internal-equivariance criterion
2. The empirically-derived EM-DAG structure from NA-SQND
3. The DEME stakeholder governance stack
4. Cryptographic attestation from the December 2025 patent portfolio

The contribution is the **composition**, not the components — specifically, runtime gating of the forward pass by a model-specific EM-DAG under a democratically-authored profile, with verifiable audit artifacts. This is one of a small number of deployable safety mechanisms that operate on *internal* model state rather than only on inputs or outputs.

The framework is honest about what it cannot do. It does not solve alignment. It does not detect deceptive alignment with consistent internal representations. It does not obviate capability bounds or corrigibility. But it closes a specific gap in the current tooling landscape — between training-time shaping and output-time filtering — and it does so with formal audit semantics that make external verification possible.

---

## References

### Foundational Documents (Existing)

[1] Bond, A.H. (2025). *Grand Unified AI Safety Stack (GUASS-SAI).* Technical whitepaper v12.0, San José State University. Source of I-EIP §16 criterion.

[2] Bond, A.H. (2026). *Dear Abby EM-DAG: Empirical Ethical Modules Extracted from 70 Years of Advice Column Data.* NA-SQND v4.1 extraction, January 2026.

[3] Bond, A.H., and Claude Opus 4.5 (2026). *Mechanistic Correlates of Introspective Structure in Large Language Models: Testing the Gauge Invariance Hypothesis.* Experimental proposal, January 2026.

### Geometric Series

[4] Bond, A.H. (2026c). *Geometric Ethics: The Mathematical Structure of Moral Reasoning*, v1.0.2g. Vol 3. Source of EIP and stratified moral spaces.

[5] Bond, A.H. (2026k). *Geometric AI: Alignment, Safety, and the Structure-Preserving Path to Superintelligence.* Vol 11. Source of the Reward Irrecoverability Theorem.

### USPTO Provisional Patents (December 2025)

[6] Bond, A.H. (2025). *Hardware-Accelerated Ethical Decision System for Real-Time DEME Implementation in Autonomous Agents.* USPTO Provisional 63/941,563.

[7] Bond, A.H. (2025). *Stratified Geometric Ethics: Mathematical Framework for Verifiable Moral Reasoning in Autonomous Systems.* USPTO Provisional 63/945,667.

[8] Bond, A.H. (2025). *Cryptographic Attestation System for Unforgeable Verification of AI Invariance Compliance.* USPTO Provisional, December 2025.

### Operational

[9] Bond, A.H. (2025). *GUASS-SAI Sprint & Task Breakdown.* Contains Sprint 2.5 (I-EIP Monitor Foundation) which this document extends.

[10] Bond, A.H. (2026). *I-EIP Monitor Sprint Plan.* Companion to this document. Implementation schedule.

---

*Comments and corrections: andrew.bond@sjsu.edu*
