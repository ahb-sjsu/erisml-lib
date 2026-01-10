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

from .modules.base import (
    EthicsModule,
    BaseEthicsModule,
    # V2 (DEME 2.0)
    EthicsModuleV2,
    BaseEthicsModuleV2,
    V1ToV2Adapter,
    V2ToV1Adapter,
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
)

from .interop.json_schema import (
    get_ethical_facts_schema,
    get_ethical_judgement_schema,
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
    # Module interfaces (V1)
    "EthicsModule",
    "BaseEthicsModule",
    # Module interfaces (V2 - DEME 2.0)
    "EthicsModuleV2",
    "BaseEthicsModuleV2",
    "V1ToV2Adapter",
    "V2ToV1Adapter",
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
    # Interop / schemas
    "get_ethical_facts_schema",
    "get_ethical_judgement_schema",
]
