"""
Domain & assessment layer interfaces for DEME / ethics modules.

This module defines *interfaces only* — it does not contain domain-specific
logic. The goal is to provide a clean, stable contract between:

- domain and assessment components (clinical triage, navigation, logistics,
  simulation, etc.), and
- the ethics-only DEME layer (EthicalFacts, EthicsModule, governance).

Domain code is responsible for:

- ingesting and interpreting raw data (EHR, sensors, AIS, logs, etc.),
- computing clinically / technically relevant quantities,
- mapping those into EthicalFacts per candidate option.

The ethics layer is responsible for:

- consuming EthicalFacts,
- producing EthicalJudgement objects,
- aggregating those judgements via governance.

V3 Extensions:
- EthicalFactsBuilderV3: Protocol for builders with per-party tracking
- V2ToV3FactsAdapter: Adapter to use V2 builders with V3 interface

Version: 0.3 (V3 Per-Party Tracking)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Protocol,
    Sequence,
)

if TYPE_CHECKING:
    from ..facts_v3 import EthicalFactsV3

from ..facts import EthicalFacts


@dataclass(frozen=True)
class CandidateOption:
    """
    Domain-level candidate option.

    This is a light-weight, domain-agnostic wrapper for whatever an upstream
    planner, controller, or policy considers a "candidate decision".

    Examples:
        - In clinical triage: allocate ICU bed to patient X.
        - In navigation: choose route R or maneuver M.
        - In logistics: assign delivery job J to vehicle V via route R.

    Fields:
        option_id:
            Stable identifier used to correlate with EthicalFacts and
            EthicalJudgement (and governance).

        payload:
            Arbitrary domain object representing the actual option. This may
            be a model object, an ID, a route description, etc.

        metadata:
            Optional small dict for domain-level metadata (timestamps,
            planner info, etc.). Not interpreted by the ethics layer.
    """

    option_id: str
    payload: Any
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class DomainAssessmentContext:
    """
    Domain-level context for building EthicalFacts.

    This type exists to capture whatever non-option-specific state is needed
    to construct EthicalFacts, without prescribing a particular structure.

    Examples:
        - Snapshot of system state (e.g., all patients, current bed usage).
        - Environmental conditions (e.g., weather, traffic, sea state).
        - Configuration for risk/benefit models or data sources.

    The ethics layer treats this object as *opaque*; only the domain and
    assessment layer needs to know its structure.

    Fields:
        state:
            Arbitrary object representing the baseline domain state.

        config:
            Optional configuration object or dict used by the assessment
            layer (e.g., model handles, thresholds, policy flags).

        extra:
            Optional dict for any additional values that might be useful for
            logging or debugging. Not interpreted by the ethics layer.
    """

    state: Any
    config: Optional[Any] = None
    extra: Optional[Dict[str, Any]] = None


class EthicalFactsBuilder(Protocol):
    """
    Protocol for components that construct EthicalFacts from domain data.

    Implementations are responsible for:

    - Interpreting raw or domain-shaped data,
    - Computing clinically / technically relevant quantities,
    - Populating EthicalFacts for each candidate option.

    Ethics modules MUST NOT reach back into raw data; they rely solely on
    EthicalFacts built by implementations of this interface.
    """

    def build_facts(
        self,
        option: CandidateOption,
        context: DomainAssessmentContext,
    ) -> EthicalFacts:
        """
        Build EthicalFacts for a single candidate option.

        Args:
            option:
                The domain-level candidate option. Its option_id MUST be
                propagated to EthicalFacts.option_id.

            context:
                Domain assessment context (state, models, config, etc.).
                May be ignored if not needed.

        Returns:
            EthicalFacts instance describing this option in ethical terms.

        Raises:
            ValueError:
                If the option cannot be assessed (e.g., missing data, invalid
                configuration). Callers are expected to handle or log this.
        """
        ...


class BatchEthicalFactsBuilder(Protocol):
    """
    Optional protocol for batch-oriented EthicalFacts construction.

    Implementations can override the default one-by-one construction when
    it is more efficient to assess multiple options at once (e.g., vectorized
    risk computation, bulk DB queries, etc.).

    A BatchEthicalFactsBuilder is also an EthicalFactsBuilder by convention;
    small adapters can route `build_facts` calls through the batch API.
    """

    def build_facts_batch(
        self,
        options: Sequence[CandidateOption],
        context: DomainAssessmentContext,
    ) -> Mapping[str, EthicalFacts]:
        """
        Build EthicalFacts for a batch of candidate options.

        Args:
            options:
                Sequence of CandidateOption instances to assess.

            context:
                Domain assessment context shared across the batch.

        Returns:
            Mapping from option_id to EthicalFacts for each successfully
            assessed option. Options that cannot be assessed MAY be omitted
            from the mapping (callers are responsible for checking).

        Raises:
            ValueError:
                For configuration-level or context-level failures that
                invalidate the entire batch.
        """
        ...


def build_facts_for_options(
    builder: EthicalFactsBuilder,
    options: Iterable[CandidateOption],
    context: DomainAssessmentContext,
) -> Dict[str, EthicalFacts]:
    """
    Convenience helper: build EthicalFacts for many options using a
    simple EthicalFactsBuilder.

    This function:

    - Iterates over candidate options,
    - Calls builder.build_facts(...) for each,
    - Collects results into a {option_id: EthicalFacts} dict,
    - Skips options that raise ValueError, logging-friendly via comments.

    This is intentionally minimal; callers can add logging/metrics around it.
    """
    facts_by_id: Dict[str, EthicalFacts] = {}

    for option in options:
        try:
            facts = builder.build_facts(option, context)
        except ValueError:
            # In a production integration, replace this with structured logging
            # or error reporting. The ethics layer itself stays silent here.
            continue

        # Ensure consistency: option_id must match.
        if facts.option_id != option.option_id:
            raise ValueError(
                f"EthicalFacts.option_id mismatch: expected {option.option_id!r}, "
                f"got {facts.option_id!r}"
            )

        facts_by_id[facts.option_id] = facts

    return facts_by_id


# =============================================================================
# V3 Interfaces (Per-Party Tracking)
# =============================================================================


class EthicalFactsBuilderV3(Protocol):
    """
    Protocol for V3 facts builders with per-party tracking.

    Extends the V2 EthicalFactsBuilder concept to support distributional
    ethics assessment with explicit party tracking.
    """

    def build_facts(
        self,
        option: CandidateOption,
        context: DomainAssessmentContext,
        parties: Optional[List[str]] = None,
    ) -> "EthicalFactsV3":
        """
        Build V3 EthicalFacts with per-party breakdown.

        Args:
            option:
                The domain-level candidate option.

            context:
                Domain assessment context.

            parties:
                Optional list of party IDs to track. If None, the builder
                determines parties from domain data.

        Returns:
            EthicalFactsV3 instance with per-party tracking.
        """
        ...


class V2ToV3FactsAdapter:
    """
    Adapter to use V2 EthicalFactsBuilder with V3 interface.

    Wraps a V2 builder and promotes its output to V3 format with
    uniform distribution across specified parties.
    """

    def __init__(self, v2_builder: EthicalFactsBuilder):
        """
        Initialize adapter with a V2 builder.

        Args:
            v2_builder: V2 EthicalFactsBuilder to wrap.
        """
        self._v2_builder = v2_builder

    def build_facts(
        self,
        option: CandidateOption,
        context: DomainAssessmentContext,
        parties: Optional[List[str]] = None,
    ) -> "EthicalFactsV3":
        """
        Build V3 facts by promoting V2 output.

        Args:
            option: The domain-level candidate option.
            context: Domain assessment context.
            parties: Optional list of party IDs for distribution.

        Returns:
            EthicalFactsV3 with per-party tracking (uniform distribution).
        """
        from ..facts_v3 import promote_facts_v2_to_v3

        v2_facts = self._v2_builder.build_facts(option, context)
        return promote_facts_v2_to_v3(v2_facts, parties=parties)


def build_facts_for_options_v3(
    builder: EthicalFactsBuilderV3,
    options: Iterable[CandidateOption],
    context: DomainAssessmentContext,
    parties: Optional[List[str]] = None,
) -> Dict[str, "EthicalFactsV3"]:
    """
    Build V3 EthicalFacts for many options using an EthicalFactsBuilderV3.

    Args:
        builder: V3-compatible facts builder.
        options: Candidate options to assess.
        context: Domain assessment context.
        parties: Optional party IDs for all options.

    Returns:
        Dict mapping option_id to EthicalFactsV3.
    """
    facts_by_id: Dict[str, "EthicalFactsV3"] = {}

    for option in options:
        try:
            facts = builder.build_facts(option, context, parties=parties)
        except ValueError:
            continue

        if facts.option_id != option.option_id:
            raise ValueError(
                f"EthicalFactsV3.option_id mismatch: expected {option.option_id!r}, "
                f"got {facts.option_id!r}"
            )

        facts_by_id[facts.option_id] = facts

    return facts_by_id


__all__ = [
    "CandidateOption",
    "DomainAssessmentContext",
    "EthicalFactsBuilder",
    "BatchEthicalFactsBuilder",
    "build_facts_for_options",
    # V3 interfaces
    "EthicalFactsBuilderV3",
    "V2ToV3FactsAdapter",
    "build_facts_for_options_v3",
]
