"""
erisml.ethics
=============

Public API for the ErisML ethics / DEME subsystem.

This package implements **DEME** (Democratically Governed Ethics Modules) for
ErisML. It is designed around a strict boundary:

- Domain & assessment layers are responsible for:
  * interpreting raw data (EHR, sensors, logs, AIS, etc.),
  * computing clinically / technically relevant quantities,
  * mapping those into EthicalFacts for each candidate option.

- Ethics modules (EMs) are responsible for:
  * consuming EthicalFacts only (no direct access to raw domain data),
  * performing purely normative reasoning,
  * emitting EthicalJudgement objects that can be aggregated via governance.

The main concepts are:

Facts & ethical dimensions
--------------------------

- ``EthicalFacts``:
    Domain-agnostic, structured envelope of ethically relevant facts for
    a single candidate option.

- Ethical dimension dataclasses (sub-structures of EthicalFacts):
    * ``Consequences``                – benefit, harm, urgency, affected_count
    * ``RightsAndDuties``             – rights, consent, explicit rules, duties
    * ``JusticeAndFairness``          – discrimination, disadvantage, power
    * ``AutonomyAndAgency``           – meaningful choice, coercion, dark patterns
    * ``PrivacyAndDataGovernance``    – privacy, data minimization, secondary use
    * ``SocietalAndEnvironmental``    – environment, long-term risk, burden
    * ``VirtueAndCare``               – compassion, trust, respect for persons
    * ``ProceduralAndLegitimacy``     – procedures, consultation, contestation
    * ``EpistemicStatus``             – uncertainty, evidence quality, novelty

Judgements & module interfaces
------------------------------

- ``Verdict``:
    Literal verdict type: one of
    ``"strongly_prefer" | "prefer" | "neutral" | "avoid" | "forbid"``.

- ``EthicalJudgement``:
    Normative assessment of a candidate option by a single EM (or governance).

- ``EthicsModule``:
    Protocol interface implemented by concrete EMs.

- ``BaseEthicsModule``:
    Convenience base class providing common functionality for EMs.

Democratic governance
---------------------

- ``GovernanceConfig``:
    Configuration for aggregating EM judgements:
    stakeholder weights, EM weights, veto EMs, thresholds, tie-breaking.

- ``DecisionOutcome``:
    Governance-level decision for a set of candidate options:
    selected option, ranked options, forbidden options, aggregated judgements.

- ``aggregate_judgements(option_id, judgements, cfg)``:
    Aggregate all EthicalJudgement objects for a single option into a
    governance-level EthicalJudgement.

- ``select_option(judgements_by_option, cfg, candidate_ids, baseline_option_id)``:
    Aggregate across options, filter forbidden / low-score options, and select
    a winner according to GovernanceConfig.

Domain & assessment interfaces
------------------------------

- ``CandidateOption``:
    Small wrapper for domain-level candidate options (id + payload).

- ``DomainAssessmentContext``:
    Opaque container for domain state/config used by assessment logic.

- ``EthicalFactsBuilder`` / ``BatchEthicalFactsBuilder``:
    Protocols for components that construct EthicalFacts from domain data.

- ``build_facts_for_options(builder, options, context)``:
    Helper to build EthicalFacts for many options with a simple builder.

Interop helpers
---------------

- ``get_ethical_facts_schema()``:
    JSON Schema (draft-07) describing the EthicalFacts structure.

- ``get_ethical_judgement_schema()``:
    JSON Schema (draft-07) describing the EthicalJudgement structure.

Serialization helpers for these types live under
``erisml.ethics.interop.serialization`` and are not re-exported here
to keep the top-level API concise.
"""

from .facts import (
    EthicalFacts,
    Consequences,
    RightsAndDuties,
    JusticeAndFairness,
    AutonomyAndAgency,
    PrivacyAndDataGovernance,
    SocietalAndEnvironmental,
    VirtueAndCare,
    ProceduralAndLegitimacy,
    EpistemicStatus,
)

from .judgement import (
    Verdict,
    EthicalJudgement,
    # V2 (DEME 2.0)
    EthicalJudgementV2,
    judgement_v1_to_v2,
    judgement_v2_to_v1,
)

# DEME V3 Judgements (Sprint 6)
from .judgement_v3 import (
    EthicalJudgementV3,
    CollapseStrategy,
    judgement_v2_to_v3,
    judgement_v3_to_v2,
    is_forbidden_v3,
    is_strongly_preferred_v3,
    get_worst_off_party,
    compute_verdict_distribution,
)

from .modules.base import (
    EthicsModule,
    BaseEthicsModule,
    # V2 (DEME 2.0)
    EthicsModuleV2,
    BaseEthicsModuleV2,
    V1ToV2Adapter,
    V2ToV1Adapter,
)

# DEME V3 Module Interfaces (Sprint 6)
from .modules.base_v3 import (
    EthicsModuleV3,
    BaseEthicsModuleV3,
    V2ToV3EMAdapter,
    V3ToV2EMAdapter,
    aggregate_party_verdicts,
    create_uniform_tensor,
)

# DEME 2.0 Core Types
from .moral_vector import MoralVector
from .moral_landscape import MoralLandscape
from .decision_proof import DecisionProof, DecisionProofChain

# DEME V3 Core Types
from .moral_tensor import (
    MoralTensor,
    SparseCOO,
    MORAL_DIMENSION_NAMES,
    DIMENSION_INDEX,
    DEFAULT_AXIS_NAMES,
)

# DEME V3 Tensor Operations
from .tensor_ops import (
    broadcast_tensors,
    stack_tensors,
    concat_tensors,
    normalize_tensor,
    clip_tensor,
    wasserstein_distance,
    cosine_similarity,
    weighted_aggregate,
)

# DEME V3 Compatibility Layer (V2/V3 Interop)
from .compat import (
    promote_v2_to_v3,
    collapse_v3_to_v2,
    ensure_tensor,
    ensure_vector,
    is_v3_compatible,
    promote_vectors_to_tensor,
    collapse_tensor_to_vectors,
)

from .governance.config import (
    GovernanceConfig,
)

from .governance.config_v2 import (
    GovernanceConfigV2,
    DimensionWeights,
)

from .governance.aggregation import (
    DecisionOutcome,
    aggregate_judgements,
    select_option,
)

from .governance.aggregation_v2 import (
    DecisionOutcomeV2,
    aggregate_moral_vectors,
    select_option_v2,
)

from .domain.interfaces import (
    CandidateOption,
    DomainAssessmentContext,
    EthicalFactsBuilder,
    BatchEthicalFactsBuilder,
    build_facts_for_options,
    # V3 interfaces
    EthicalFactsBuilderV3,
    V2ToV3FactsAdapter,
    build_facts_for_options_v3,
)

# DEME V3 Facts (Per-Party Tracking)
from .facts_v3 import (
    # Per-party dataclasses
    PartyConsequences,
    PartyRights,
    PartyJustice,
    PartyAutonomy,
    PartyPrivacy,
    PartySocietal,
    PartyVirtue,
    PartyProcedural,
    # V3 dimension dataclasses
    ConsequencesV3,
    RightsAndDutiesV3,
    JusticeAndFairnessV3,
    AutonomyAndAgencyV3,
    PrivacyAndDataGovernanceV3,
    SocietalAndEnvironmentalV3,
    VirtueAndCareV3,
    ProceduralAndLegitimacyV3,
    EpistemicStatusV3,
    # V3 container
    EthicalFactsV3,
    # V2↔V3 conversion
    promote_facts_v2_to_v3,
    collapse_facts_v3_to_v2,
)

from .interop.json_schema import (
    get_ethical_facts_schema,
    get_ethical_judgement_schema,
)

# DEME V3 Fairness Metrics (Sprint 5)
from .fairness_metrics import (
    gini_coefficient,
    rawlsian_maximin,
    rawlsian_maximin_welfare,
    utilitarian_sum,
    utilitarian_average,
    prioritarian_weighted_welfare,
    extract_vulnerability_weights,
    atkinson_index,
    theil_index,
    theil_decomposition,
    FairnessMetrics,
)

# DEME V3 Temporal Operations (Sprint 7)
from .temporal_ops import (
    TimeMetadata,
    validate_temporal_tensor,
    is_temporal_tensor,
    apply_temporal_discount,
    temporal_aggregate,
    IrreversibilityResult,
    detect_irreversibility,
    dtw_distance,
    trajectory_similarity,
    slice_time_window,
    sliding_window,
    rolling_aggregate,
    compute_temporal_trend,
    detect_trend_reversal,
)

# DEME V3 Coalition Context (Sprint 8)
from .coalition import (
    Coalition,
    CoalitionStructure,
    ActionProfile,
    CoalitionContext,
    SparseCoalitionTensor,
    CoalitionStabilityResult,
    check_coalition_stability,
    slice_by_action,
    slice_by_coalition,
    slice_by_action_profile,
    create_coalition_tensor,
    create_uniform_coalition_tensor,
    aggregate_over_coalitions,
    aggregate_over_actions,
)

# DEME V3 Game Theory (Sprint 9)
from .game_theory import (
    ShapleyValues,
    ContributionMargins,
    CoreStabilityResult,
    NucleolusResult,
    ShapleyAttribution,
    compute_shapley_exact,
    compute_shapley_monte_carlo,
    compute_shapley_from_tensor,
    compute_contribution_margins,
    check_core_stability,
    is_core_empty,
    compute_nucleolus,
    compute_ethical_attribution,
    create_voting_game,
    create_additive_game,
    create_superadditive_game,
)

# DEME V3 Strategic Layer (Sprint 10)
from .layers.strategic import (
    # V2 compatible types
    StakeholderFeedback,
    ProfileUpdate,
    StrategicLayerConfig,
    StrategicLayer,
    # V3 types
    EquilibriumType,
    StrategyProfile,
    NashEquilibriumResult,
    CoalitionStabilityAnalysis,
    PolicyRecommendation,
    StrategicAnalysisResult,
)

# DEME V3 Acceleration Framework (Sprint 11)
from .acceleration import (
    # Core abstractions
    AccelerationBackend,
    DeviceInfo,
    DeviceType,
    TensorHandle,
    # CPU backend
    CPUBackend,
    get_cpu_backend,
    # Dispatcher
    AccelerationDispatcher,
    BackendPreference,
    DispatcherConfig,
    get_dispatcher,
    get_backend,
    list_backends,
)

# DEME V3 CUDA Backend (Sprint 12 - optional)
from .acceleration import (
    CUDABackend,
    cuda_is_available,
    get_cuda_backend,
    HAS_CUPY,
)

# DEME V3 Jetson Backend (Sprint 13 - optional)
from .acceleration import (
    JetsonBackend,
    JetsonConfig,
    JetsonPowerMode,
    DLACore,
    jetson_is_available,
    get_jetson_model,
    get_jetson_backend,
    HAS_JETSON,
    HAS_TENSORRT,
)

# DEME V3 Uncertainty Quantification (Sprint 14)
from .uncertainty import (
    DistributionType,
    AggregationMethod,
    UncertaintyBounds,
    UncertainValue,
    UncertaintyAnalysis,
    generate_samples,
    generate_moral_samples,
    expected_value,
    variance,
    std_dev,
    percentiles,
    confidence_interval,
    cvar,
    cvar_upper,
    worst_case,
    best_case,
    value_at_risk,
    aggregate_samples,
    analyze_uncertainty,
    propagate_uncertainty,
    compare_under_uncertainty,
    stochastic_dominance,
)

# DEME V3 Tensor Decomposition (Sprint 15)
from .tensor_decomposition import (
    DecompositionType,
    MemoryLayout,
    TuckerDecomposition,
    TensorTrainDecomposition,
    HierarchicalSparseTensor,
    SparseBlock,
    OptimizedTensor,
    validate_rank6_shape,
    create_rank6_tensor,
    estimate_memory_usage,
    recommend_decomposition,
    compress_tensor,
    decompose_for_backend,
    reconstruct_from_decomposition,
)

__all__ = [
    # Facts & ethical dimensions
    "EthicalFacts",
    "Consequences",
    "RightsAndDuties",
    "JusticeAndFairness",
    "AutonomyAndAgency",
    "PrivacyAndDataGovernance",
    "SocietalAndEnvironmental",
    "VirtueAndCare",
    "ProceduralAndLegitimacy",
    "EpistemicStatus",
    # Judgements & verdicts (V1)
    "Verdict",
    "EthicalJudgement",
    # Judgements (V2 - DEME 2.0)
    "EthicalJudgementV2",
    "judgement_v1_to_v2",
    "judgement_v2_to_v1",
    # Judgements (V3 - DEME V3 Sprint 6)
    "EthicalJudgementV3",
    "CollapseStrategy",
    "judgement_v2_to_v3",
    "judgement_v3_to_v2",
    "is_forbidden_v3",
    "is_strongly_preferred_v3",
    "get_worst_off_party",
    "compute_verdict_distribution",
    # Module interfaces (V1)
    "EthicsModule",
    "BaseEthicsModule",
    # Module interfaces (V2 - DEME 2.0)
    "EthicsModuleV2",
    "BaseEthicsModuleV2",
    "V1ToV2Adapter",
    "V2ToV1Adapter",
    # Module interfaces (V3 - DEME V3 Sprint 6)
    "EthicsModuleV3",
    "BaseEthicsModuleV3",
    "V2ToV3EMAdapter",
    "V3ToV2EMAdapter",
    "aggregate_party_verdicts",
    "create_uniform_tensor",
    # DEME 2.0 Core Types
    "MoralVector",
    "MoralLandscape",
    "DecisionProof",
    "DecisionProofChain",
    # DEME V3 Core Types
    "MoralTensor",
    "SparseCOO",
    "MORAL_DIMENSION_NAMES",
    "DIMENSION_INDEX",
    "DEFAULT_AXIS_NAMES",
    # DEME V3 Tensor Operations
    "broadcast_tensors",
    "stack_tensors",
    "concat_tensors",
    "normalize_tensor",
    "clip_tensor",
    "wasserstein_distance",
    "cosine_similarity",
    "weighted_aggregate",
    # DEME V3 Compatibility Layer
    "promote_v2_to_v3",
    "collapse_v3_to_v2",
    "ensure_tensor",
    "ensure_vector",
    "is_v3_compatible",
    "promote_vectors_to_tensor",
    "collapse_tensor_to_vectors",
    # Governance (V1)
    "GovernanceConfig",
    "DecisionOutcome",
    "aggregate_judgements",
    "select_option",
    # Governance (V2 - DEME 2.0)
    "GovernanceConfigV2",
    "DimensionWeights",
    "DecisionOutcomeV2",
    "aggregate_moral_vectors",
    "select_option_v2",
    # Domain & assessment interfaces
    "CandidateOption",
    "DomainAssessmentContext",
    "EthicalFactsBuilder",
    "BatchEthicalFactsBuilder",
    "build_facts_for_options",
    # Domain & assessment interfaces (V3)
    "EthicalFactsBuilderV3",
    "V2ToV3FactsAdapter",
    "build_facts_for_options_v3",
    # DEME V3 Facts - Per-party dataclasses
    "PartyConsequences",
    "PartyRights",
    "PartyJustice",
    "PartyAutonomy",
    "PartyPrivacy",
    "PartySocietal",
    "PartyVirtue",
    "PartyProcedural",
    # DEME V3 Facts - Dimension dataclasses
    "ConsequencesV3",
    "RightsAndDutiesV3",
    "JusticeAndFairnessV3",
    "AutonomyAndAgencyV3",
    "PrivacyAndDataGovernanceV3",
    "SocietalAndEnvironmentalV3",
    "VirtueAndCareV3",
    "ProceduralAndLegitimacyV3",
    "EpistemicStatusV3",
    # DEME V3 Facts - Container & conversion
    "EthicalFactsV3",
    "promote_facts_v2_to_v3",
    "collapse_facts_v3_to_v2",
    # Interop / schemas
    "get_ethical_facts_schema",
    "get_ethical_judgement_schema",
    # DEME V3 Fairness Metrics (Sprint 5)
    "gini_coefficient",
    "rawlsian_maximin",
    "rawlsian_maximin_welfare",
    "utilitarian_sum",
    "utilitarian_average",
    "prioritarian_weighted_welfare",
    "extract_vulnerability_weights",
    "atkinson_index",
    "theil_index",
    "theil_decomposition",
    "FairnessMetrics",
    # DEME V3 Temporal Operations (Sprint 7)
    "TimeMetadata",
    "validate_temporal_tensor",
    "is_temporal_tensor",
    "apply_temporal_discount",
    "temporal_aggregate",
    "IrreversibilityResult",
    "detect_irreversibility",
    "dtw_distance",
    "trajectory_similarity",
    "slice_time_window",
    "sliding_window",
    "rolling_aggregate",
    "compute_temporal_trend",
    "detect_trend_reversal",
    # DEME V3 Coalition Context (Sprint 8)
    "Coalition",
    "CoalitionStructure",
    "ActionProfile",
    "CoalitionContext",
    "SparseCoalitionTensor",
    "CoalitionStabilityResult",
    "check_coalition_stability",
    "slice_by_action",
    "slice_by_coalition",
    "slice_by_action_profile",
    "create_coalition_tensor",
    "create_uniform_coalition_tensor",
    "aggregate_over_coalitions",
    "aggregate_over_actions",
    # DEME V3 Game Theory (Sprint 9)
    "ShapleyValues",
    "ContributionMargins",
    "CoreStabilityResult",
    "NucleolusResult",
    "ShapleyAttribution",
    "compute_shapley_exact",
    "compute_shapley_monte_carlo",
    "compute_shapley_from_tensor",
    "compute_contribution_margins",
    "check_core_stability",
    "is_core_empty",
    "compute_nucleolus",
    "compute_ethical_attribution",
    "create_voting_game",
    "create_additive_game",
    "create_superadditive_game",
    # DEME V3 Strategic Layer (Sprint 10)
    "StakeholderFeedback",
    "ProfileUpdate",
    "StrategicLayerConfig",
    "StrategicLayer",
    "EquilibriumType",
    "StrategyProfile",
    "NashEquilibriumResult",
    "CoalitionStabilityAnalysis",
    "PolicyRecommendation",
    "StrategicAnalysisResult",
    # DEME V3 Acceleration Framework (Sprint 11)
    "AccelerationBackend",
    "DeviceInfo",
    "DeviceType",
    "TensorHandle",
    "CPUBackend",
    "get_cpu_backend",
    "AccelerationDispatcher",
    "BackendPreference",
    "DispatcherConfig",
    "get_dispatcher",
    "get_backend",
    "list_backends",
    # DEME V3 CUDA Backend (Sprint 12)
    "CUDABackend",
    "cuda_is_available",
    "get_cuda_backend",
    "HAS_CUPY",
    # DEME V3 Jetson Backend (Sprint 13)
    "JetsonBackend",
    "JetsonConfig",
    "JetsonPowerMode",
    "DLACore",
    "jetson_is_available",
    "get_jetson_model",
    "get_jetson_backend",
    "HAS_JETSON",
    "HAS_TENSORRT",
    # DEME V3 Uncertainty Quantification (Sprint 14)
    "DistributionType",
    "AggregationMethod",
    "UncertaintyBounds",
    "UncertainValue",
    "UncertaintyAnalysis",
    "generate_samples",
    "generate_moral_samples",
    "expected_value",
    "variance",
    "std_dev",
    "percentiles",
    "confidence_interval",
    "cvar",
    "cvar_upper",
    "worst_case",
    "best_case",
    "value_at_risk",
    "aggregate_samples",
    "analyze_uncertainty",
    "propagate_uncertainty",
    "compare_under_uncertainty",
    "stochastic_dominance",
    # DEME V3 Tensor Decomposition (Sprint 15)
    "DecompositionType",
    "MemoryLayout",
    "TuckerDecomposition",
    "TensorTrainDecomposition",
    "HierarchicalSparseTensor",
    "SparseBlock",
    "OptimizedTensor",
    "validate_rank6_shape",
    "create_rank6_tensor",
    "estimate_memory_usage",
    "recommend_decomposition",
    "compress_tensor",
    "decompose_for_backend",
    "reconstruct_from_decomposition",
]
