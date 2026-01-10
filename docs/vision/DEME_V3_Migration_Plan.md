# DEME V3 Migration Plan: Multi-Agent Ethics with Rank 4-6 Tensors

**Version**: 1.0
**Date**: January 2026
**Status**: Planning Phase

---

## Executive Summary

DEME V3 represents a significant architectural evolution from the current V2 vector-based (rank-1) ethics system to a comprehensive multi-agent ethics framework utilizing rank 4-6 tensors. This migration enables:

- **Distributional Justice**: Per-agent/party impact tracking across ethical dimensions
- **Temporal Moral Dynamics**: Time-evolving ethical constraints
- **Coalition Formation**: Game-theoretic multi-agent coordination
- **Contextual Interactions**: Environment-dependent ethical trade-offs
- **Uncertainty Quantification**: Robust decision-making under epistemic uncertainty
- **Hardware Acceleration**: Optional Jetson Nano GPU/EPU support for edge deployment

---

## 1. Current State Analysis (V2)

### 1.1 V2 Architecture Summary

The current DEME 2.0 implementation provides:

| Component | V2 Implementation | Limitation |
|-----------|-------------------|------------|
| MoralVector | 9-dimensional rank-1 tensor | Cannot model per-party distributions |
| EthicalFacts | Aggregate scalar values | No party-specific impact tracking |
| EthicsModuleV2 | Single MoralVector output | No multi-agent coordination |
| Governance | Tier-based aggregation | No coalition stability analysis |
| Three-Layer Pipeline | Reflex/Tactical/Strategic | Strategic layer placeholder only |

### 1.2 V2 Performance Baseline

| Operation | Current Latency | Target (V3) |
|-----------|-----------------|-------------|
| Reflex veto check | 35ns | <100ns |
| Vector scalarization | 50ns | <500ns |
| Full tactical decision | 10-100ms | <150ms |
| Decision proof generation | 5ms | <10ms |

### 1.3 Key Files Requiring Migration

```
src/erisml/ethics/
├── facts.py                    # EthicalFacts → TensorEthicalFacts
├── moral_vector.py             # MoralVector → MoralTensor
├── moral_landscape.py          # MoralLandscape → TensorLandscape
├── judgement.py                # EthicalJudgementV2 → EthicalJudgementV3
├── modules/base.py             # BaseEthicsModuleV2 → BaseEthicsModuleV3
├── governance/aggregation_v2.py # Vector → Tensor aggregation
├── governance/config_v2.py     # DimensionWeights → InteractionTensors
├── layers/reflex.py            # Extend for tensor veto
├── layers/tactical.py          # Tensor-aware tactical reasoning
├── layers/strategic.py         # Full implementation (coalition analysis)
└── decision_proof.py           # Tensor hashing and audit trails
```

---

## 2. V3 Architecture Goals

### 2.1 Tensor Hierarchy

V3 introduces a progressive tensor hierarchy:

| Rank | Name | Shape | Use Case |
|------|------|-------|----------|
| 1 | MoralVector | (k,) | Backward compatibility, simple scenarios |
| 2 | DistributionalTensor | (k, n) | Per-party impact distribution |
| 3 | TemporalTensor | (k, n, τ) | Time-evolving ethics |
| 4 | CoalitionTensor | (k, n, a, c) | Multi-agent action coordination |
| 5 | UncertaintyTensor | (k, n, τ, s) | Monte Carlo uncertainty samples |
| 6 | FullContextTensor | (k, n, τ, a, c, s) | Complete ethical state space |

Where:
- **k** = 9 ethical dimensions (harm, rights, fairness, autonomy, privacy, societal, virtue, legitimacy, epistemic)
- **n** = number of affected parties/agents
- **τ** = time steps
- **a** = action space size
- **c** = coalition configurations (up to 2^n, typically sparse)
- **s** = uncertainty samples

### 2.2 Multi-Agent Ethics Capabilities

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEME V3 Multi-Agent Architecture              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Agent 1    │    │   Agent 2    │    │   Agent N    │       │
│  │  (EM Set 1)  │    │  (EM Set 2)  │    │  (EM Set N)  │       │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Coalition Formation Layer                   │    │
│  │  - Shapley value computation                            │    │
│  │  - Nash equilibrium detection                           │    │
│  │  - Pareto coalition identification                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Tensor Aggregation Engine                   │    │
│  │  - Rank-aware contraction                               │    │
│  │  - Sparse tensor optimization                           │    │
│  │  - GPU/EPU acceleration (Jetson Nano)                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                     │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Decision & Proof Generation                 │    │
│  │  - Tensor hash chains                                   │    │
│  │  - Coalition stability certificates                     │    │
│  │  - Distributional fairness proofs                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Core Design Principles

1. **Backward Compatibility**: V2 MoralVector treated as rank-1 MoralTensor
2. **Progressive Complexity**: Start with rank-2, add higher ranks incrementally
3. **Sparse by Default**: Use COO/CSR formats for memory efficiency
4. **Hardware Agnostic**: CPU fallback with optional GPU/EPU acceleration
5. **Type Safety**: Full typing with runtime validation
6. **Audit Complete**: All tensor operations logged for decision proofs

---

## 3. Technical Design

### 3.1 MoralTensor Core Class

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Union, Tuple
import numpy as np

@dataclass
class MoralTensor:
    """
    Multi-dimensional ethical assessment tensor supporting ranks 1-6.

    Rank semantics:
        1: (k,)           - Standard moral vector (V2 compatible)
        2: (k, n)         - Distributional (per-party)
        3: (k, n, τ)      - Temporal evolution
        4: (k, n, a, c)   - Coalition actions
        5: (k, n, τ, s)   - Uncertainty samples
        6: (k, n, τ, a, c, s) - Full context
    """

    # Core tensor data (dense or sparse representation)
    data: np.ndarray

    # Tensor metadata
    rank: int
    shape: Tuple[int, ...]
    dimension_names: Tuple[str, ...] = field(default_factory=lambda: (
        "physical_harm", "rights_respect", "fairness_equity",
        "autonomy_respect", "privacy_protection", "societal_environmental",
        "virtue_care", "legitimacy_trust", "epistemic_quality"
    ))

    # Party/agent tracking (for rank >= 2)
    party_ids: Optional[List[str]] = None
    party_vulnerabilities: Optional[Dict[str, float]] = None

    # Temporal metadata (for rank >= 3)
    time_steps: Optional[List[float]] = None
    discount_factor: float = 0.95

    # Action/coalition metadata (for rank >= 4)
    action_ids: Optional[List[str]] = None
    coalition_configs: Optional[List[Tuple[str, ...]]] = None

    # Uncertainty metadata (for rank >= 5)
    sample_count: int = 0
    confidence_level: float = 0.95

    # Veto and audit
    veto_flags: List[str] = field(default_factory=list)
    veto_locations: List[Tuple[int, ...]] = field(default_factory=list)
    reason_codes: List[str] = field(default_factory=list)

    # Sparse representation (optional)
    is_sparse: bool = False
    sparse_indices: Optional[np.ndarray] = None
    sparse_values: Optional[np.ndarray] = None

    # Hardware acceleration hint
    device: str = "cpu"  # "cpu", "cuda", "jetson"

    def to_vector(self, aggregation: str = "worst_case") -> "MoralVector":
        """Collapse to V2-compatible MoralVector."""
        ...

    def slice_party(self, party_id: str) -> "MoralTensor":
        """Extract tensor slice for specific party."""
        ...

    def slice_time(self, t: int) -> "MoralTensor":
        """Extract tensor slice at specific time step."""
        ...

    def contract(self, axis: int, weights: np.ndarray) -> "MoralTensor":
        """Weighted contraction along specified axis."""
        ...

    def gini_coefficient(self, dimension: str) -> float:
        """Compute Gini coefficient for distributional fairness."""
        ...

    def worst_off(self, dimension: str) -> Tuple[str, float]:
        """Find worst-off party for Rawlsian maximin."""
        ...

    def pareto_dominated_parties(self) -> List[str]:
        """Identify parties dominated across all dimensions."""
        ...
```

### 3.2 Extended EthicalFacts

```python
@dataclass
class ConsequencesV3:
    """V3 consequences with per-party distribution."""

    # Aggregate values (V2 compatible)
    expected_benefit: float
    expected_harm: float
    affected_party_count: int
    urgency: float

    # Per-party distributions (V3)
    benefit_per_party: Dict[str, float] = field(default_factory=dict)
    harm_per_party: Dict[str, float] = field(default_factory=dict)
    party_vulnerabilities: Dict[str, float] = field(default_factory=dict)

    # Temporal projections (V3)
    harm_trajectory: Optional[Dict[str, List[float]]] = None  # party_id → [harm_t0, harm_t1, ...]
    benefit_trajectory: Optional[Dict[str, List[float]]] = None


@dataclass
class EthicalFactsV3:
    """V3 ethical facts with multi-agent and temporal support."""

    option_id: str

    # Core fact categories (V2 compatible structure, V3 content)
    consequences: ConsequencesV3
    rights_and_duties: RightsAndDutiesV3
    justice_and_fairness: JusticeAndFairnessV3

    # Optional specializations
    autonomy_and_agency: Optional[AutonomyAndAgencyV3] = None
    privacy_and_data: Optional[PrivacyAndDataGovernanceV3] = None
    societal_and_environmental: Optional[SocietalAndEnvironmentalV3] = None
    virtue_and_care: Optional[VirtueAndCareV3] = None
    procedural_and_legitimacy: Optional[ProceduralAndLegitimacyV3] = None
    epistemic_status: Optional[EpistemicStatusV3] = None

    # Multi-agent context (V3)
    acting_agent_id: str = "default"
    affected_parties: List[str] = field(default_factory=list)
    coalition_context: Optional[CoalitionContext] = None

    # Temporal context (V3)
    decision_horizon: int = 1  # number of time steps
    time_step_duration: float = 1.0  # seconds per step

    tags: Optional[List[str]] = None
    extra: Optional[Dict[str, Any]] = None
```

### 3.3 EthicsModule V3 Protocol

```python
@runtime_checkable
class EthicsModuleV3(Protocol):
    """V3 ethics module with tensor output."""

    em_name: str
    stakeholder: str
    em_tier: int
    supported_ranks: Tuple[int, ...]  # e.g., (1, 2, 3) for ranks supported

    def judge(self, facts: EthicalFactsV3) -> "EthicalJudgementV3":
        """Full tensor-based ethical judgement."""
        ...

    def judge_distributed(
        self,
        facts: EthicalFactsV3,
        target_rank: int = 2
    ) -> "EthicalJudgementV3":
        """Produce judgement at specified tensor rank."""
        ...

    def reflex_check(self, facts: EthicalFactsV3) -> Optional[bool]:
        """Fast constitutional veto (inherited from V2)."""
        ...

    def coalition_contribution(
        self,
        facts: EthicalFactsV3,
        coalition: Tuple[str, ...]
    ) -> float:
        """Marginal ethical value contribution to coalition."""
        ...
```

### 3.4 Tensor Aggregation Engine

```python
class TensorAggregationEngine:
    """
    Aggregates multi-agent tensor judgements with configurable strategies.
    """

    def __init__(
        self,
        config: GovernanceConfigV3,
        device: str = "cpu",
        use_sparse: bool = True,
    ):
        self.config = config
        self.device = device
        self.use_sparse = use_sparse
        self._init_acceleration()

    def _init_acceleration(self):
        """Initialize hardware acceleration if available."""
        if self.device == "jetson":
            self._init_jetson()
        elif self.device == "cuda":
            self._init_cuda()

    def aggregate(
        self,
        judgements: List[EthicalJudgementV3],
        strategy: AggregationStrategy = AggregationStrategy.WEIGHTED_MEAN,
    ) -> MoralTensor:
        """
        Aggregate multiple EM judgements into single tensor.

        Handles mixed-rank inputs via promotion to highest rank.
        """
        ...

    def compute_shapley_values(
        self,
        coalition_tensor: MoralTensor,
        dimension: str,
    ) -> Dict[str, float]:
        """Compute Shapley values for fair credit assignment."""
        ...

    def find_stable_coalitions(
        self,
        coalition_tensor: MoralTensor,
    ) -> List[Tuple[str, ...]]:
        """Find coalitions satisfying stability criteria."""
        ...

    def pareto_frontier(
        self,
        tensors: List[MoralTensor],
    ) -> List[int]:
        """Find Pareto-optimal options across tensor space."""
        ...
```

---

## 4. Jetson Nano GPU/EPU Acceleration

### 4.1 Hardware Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEME V3 Acceleration Layer                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  Acceleration Dispatcher                 │    │
│  │  - Device detection (CPU/CUDA/Jetson)                   │    │
│  │  - Automatic fallback chain                             │    │
│  │  - Memory management                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                    │                    │              │
│         ▼                    ▼                    ▼              │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐         │
│  │    CPU     │      │   CUDA     │      │  Jetson    │         │
│  │  Backend   │      │  Backend   │      │  Backend   │         │
│  │            │      │            │      │            │         │
│  │ - NumPy    │      │ - CuPy     │      │ - TensorRT │         │
│  │ - SciPy    │      │ - PyTorch  │      │ - cuDLA    │         │
│  │   sparse   │      │   CUDA     │      │ - PVA      │         │
│  └────────────┘      └────────────┘      └────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Jetson Nano Specific Optimizations

```python
# src/erisml/ethics/acceleration/jetson.py

class JetsonAccelerator:
    """
    NVIDIA Jetson Nano acceleration for DEME tensor operations.

    Supports:
    - Jetson Nano (4GB): 128 CUDA cores, Maxwell GPU
    - Jetson Nano Orin: 1024 CUDA cores + 2 NVDLA engines
    - Jetson AGX Orin: Full acceleration suite
    """

    def __init__(self, config: JetsonConfig):
        self.config = config
        self.device_info = self._detect_jetson()
        self._init_tensorrt()
        self._init_dla_if_available()

    def _detect_jetson(self) -> JetsonDeviceInfo:
        """Detect Jetson model and capabilities."""
        ...

    def _init_tensorrt(self):
        """Initialize TensorRT for optimized inference."""
        ...

    def _init_dla_if_available(self):
        """Initialize Deep Learning Accelerator on Orin devices."""
        ...

    def tensor_contract(
        self,
        tensor: MoralTensor,
        axis: int,
        weights: np.ndarray,
    ) -> MoralTensor:
        """GPU-accelerated tensor contraction."""
        ...

    def batch_veto_check(
        self,
        tensors: List[MoralTensor],
        thresholds: Dict[str, float],
    ) -> List[bool]:
        """Parallel veto checking across multiple tensors."""
        ...

    def sparse_aggregate(
        self,
        sparse_tensors: List[MoralTensor],
        strategy: AggregationStrategy,
    ) -> MoralTensor:
        """Sparse tensor aggregation optimized for Jetson."""
        ...


@dataclass
class JetsonConfig:
    """Configuration for Jetson acceleration."""

    # Device selection
    prefer_dla: bool = True  # Use DLA when available (Orin)
    fallback_to_gpu: bool = True
    fallback_to_cpu: bool = True

    # Memory management
    max_gpu_memory_mb: int = 2048  # Conservative for Nano 4GB
    use_unified_memory: bool = True

    # TensorRT optimization
    tensorrt_precision: str = "fp16"  # "fp32", "fp16", "int8"
    tensorrt_workspace_mb: int = 512
    cache_optimized_engines: bool = True

    # Batch processing
    optimal_batch_size: int = 32
    max_batch_size: int = 128

    # Power management
    power_mode: str = "maxn"  # "maxn", "15w", "10w"
```

### 4.3 EPU (Edge Processing Unit) Support

For future Jetson models with dedicated EPU:

```python
class EPUAccelerator:
    """
    Edge Processing Unit acceleration for ultra-low-latency ethics.

    Targets sub-microsecond reflex layer operations.
    """

    def __init__(self, config: EPUConfig):
        self.config = config
        self._init_epu_runtime()

    def reflex_veto_check(
        self,
        tensor: MoralTensor,
        constitutional_thresholds: Dict[str, float],
    ) -> Tuple[bool, Optional[str]]:
        """
        Ultra-fast constitutional veto check.
        Target: <1μs latency
        """
        ...

    def precompile_veto_rules(
        self,
        rules: List[VetoRule],
    ) -> EPUProgram:
        """Compile veto rules to EPU bytecode."""
        ...
```

### 4.4 Performance Targets with Acceleration

| Operation | CPU | CUDA | Jetson Nano | Jetson Orin |
|-----------|-----|------|-------------|-------------|
| Rank-2 veto check | 150ns | 50ns | 80ns | 40ns |
| Rank-4 contraction | 10μs | 1μs | 3μs | 0.8μs |
| Rank-6 aggregation | 500μs | 50μs | 150μs | 30μs |
| Shapley computation | 100ms | 10ms | 30ms | 5ms |
| Coalition stability | 500ms | 50ms | 150ms | 25ms |

---

## 5. Migration Strategy

### 5.1 Phased Rollout

```
Phase 1: Foundation (Sprints 1-3)
├── MoralTensor core implementation
├── V2 → V3 compatibility layer
├── Basic CPU tensor operations
└── Unit test infrastructure

Phase 2: Rank-2 Distributional (Sprints 4-6)
├── EthicalFactsV3 with per-party tracking
├── DistributionalTensor operations
├── Gini coefficient and fairness metrics
└── Integration tests

Phase 3: Rank-3/4 Multi-Agent (Sprints 7-10)
├── Temporal tensor support
├── Coalition formation algorithms
├── Shapley value computation
└── Strategic layer implementation

Phase 4: Hardware Acceleration (Sprints 11-13)
├── CUDA backend
├── Jetson Nano integration
├── TensorRT optimization
└── Performance benchmarks

Phase 5: Rank-5/6 Advanced (Sprints 14-16)
├── Uncertainty quantification
├── Full context tensors
├── Monte Carlo integration
└── Robustness certification

Phase 6: Production Hardening (Sprints 17-18)
├── Comprehensive test suite
├── Documentation
├── Migration tooling
└── Performance tuning
```

### 5.2 Backward Compatibility

```python
# Automatic V2 → V3 promotion
def promote_v2_to_v3(
    vector: MoralVector,
    party_count: int = 1,
) -> MoralTensor:
    """
    Promote V2 MoralVector to V3 MoralTensor.

    Default: Rank-2 tensor with uniform distribution across parties.
    """
    data = np.tile(vector.to_array(), (party_count, 1)).T
    return MoralTensor(
        data=data,
        rank=2,
        shape=(9, party_count),
        party_ids=[f"party_{i}" for i in range(party_count)],
        veto_flags=vector.veto_flags,
        reason_codes=vector.reason_codes,
    )

# V3 → V2 collapse for legacy consumers
def collapse_v3_to_v2(
    tensor: MoralTensor,
    collapse_strategy: str = "worst_case",
) -> MoralVector:
    """
    Collapse V3 MoralTensor to V2 MoralVector.

    Strategies:
    - "worst_case": min across all parties
    - "average": mean across all parties
    - "weighted": vulnerability-weighted average
    """
    ...
```

---

## 6. Testing Strategy

### 6.1 Test Categories

| Category | Purpose | Target Coverage |
|----------|---------|-----------------|
| Unit Tests | Individual tensor operations | 95% |
| Integration Tests | Multi-component workflows | 85% |
| Compatibility Tests | V2 ↔ V3 round-trip | 100% |
| Performance Tests | Latency and throughput | All critical paths |
| Hardware Tests | CPU/CUDA/Jetson parity | Platform matrix |
| Invariance Tests | Bond Index compliance | All EMs |

### 6.2 Bond Index Extension for Tensors

```python
class TensorBondInvarianceTest:
    """
    Extended Bond Index testing for tensor representations.

    Additional transforms for multi-agent scenarios:
    - party_reorder: Permute party indices
    - coalition_relabel: Rename coalition configurations
    - temporal_shift: Offset time indices
    - sparse_densify: Convert sparse ↔ dense
    """

    TENSOR_TRANSFORMS = [
        "party_reorder",
        "coalition_relabel",
        "temporal_shift",
        "sparse_densify",
        "rank_promotion",  # e.g., rank-2 → rank-3 with singleton time
        "dimension_permute",
    ]
```

---

## 7. Risk Assessment

### 7.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Tensor complexity explosion | Medium | High | Sparse representations, low-rank approximations |
| GPU memory limitations | Medium | Medium | Streaming, chunked processing |
| Jetson SDK compatibility | Low | Medium | Version pinning, fallback paths |
| V2 API breaking changes | Low | High | Comprehensive compatibility layer |
| Performance regression | Medium | Medium | Continuous benchmarking |

### 7.2 Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Coalition algorithm complexity | High | Medium | Simplify to 2-agent first |
| Hardware availability | Low | Low | Cloud Jetson instances |
| Research dependencies | Medium | Medium | Parallel research track |

---

## 8. Success Criteria

### 8.1 Functional Requirements

- [ ] MoralTensor supports ranks 1-6
- [ ] V2 MoralVector fully interoperable
- [ ] EthicalFactsV3 tracks per-party impacts
- [ ] EthicsModuleV3 protocol implemented
- [ ] Coalition formation with Shapley values
- [ ] Temporal ethics with discounting
- [ ] Decision proofs include tensor hashes

### 8.2 Performance Requirements

- [ ] Rank-2 operations < 500ns (CPU)
- [ ] Rank-4 operations < 50μs (CPU)
- [ ] Jetson Nano acceleration > 3x speedup
- [ ] Memory usage < 2x V2 baseline
- [ ] No regressions in V2 compatibility mode

### 8.3 Quality Requirements

- [ ] 90%+ code coverage
- [ ] Bond Index < 0.1 for all standard EMs
- [ ] Full type annotations
- [ ] API documentation complete
- [ ] Migration guide published

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **MoralTensor** | Multi-dimensional ethical assessment with rank 1-6 |
| **Rank** | Number of tensor dimensions (indices) |
| **Coalition** | Subset of agents acting together |
| **Shapley Value** | Fair credit assignment in cooperative games |
| **Bond Index** | Measure of representational coherence |
| **EPU** | Edge Processing Unit for ultra-low-latency inference |
| **DLA** | Deep Learning Accelerator (Jetson Orin) |

---

## Appendix B: Related Documents

- [DEME 2.0 Vision Paper](./DEME_2.0_Vision_Paper.md)
- [DEME 3.0 Tensorial Ethics Vision](./DEME_3.0_Tensorial_Ethics_Vision.md)
- [Tensorial Ethics Mathematical Foundations](../papers/foundations/Tensorial%20Ethics.pdf)
- [Bond Invariance Principle](./Bond_Invariance_Principle.md)
- [Dear Abby Empirical Analysis](./Dear_Abby_Empirical_Ethics_Analysis.md)

---

*Document maintained by the ErisML Core Team*
