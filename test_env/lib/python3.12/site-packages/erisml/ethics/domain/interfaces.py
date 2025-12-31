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

Version: 0.2 (EthicalDomains update)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional, Protocol, Sequence

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


__all__ = [
    "CandidateOption",
    "DomainAssessmentContext",
    "EthicalFactsBuilder",
    "BatchEthicalFactsBuilder",
    "build_facts_for_options",
]
