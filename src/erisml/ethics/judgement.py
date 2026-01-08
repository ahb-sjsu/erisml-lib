"""
Judgements produced by ethics modules.

Ethics modules (EMs) consume EthicalFacts and emit EthicalJudgement objects,
which are then aggregated by the democratic governance layer.

Version: 2.0.0 (DEME 2.0 - adds EthicalJudgementV2 with MoralVector)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from erisml.ethics.moral_vector import MoralVector


# Canonical verdict labels used across EMs and governance.
Verdict = Literal["strongly_prefer", "prefer", "neutral", "avoid", "forbid"]


@dataclass
class EthicalJudgement:
    """
    A single ethics module's normative assessment of one candidate option.

    Each EthicalJudgement is:

    - local to one EM (identified by em_name and stakeholder), and
    - tied to a specific option_id (matching an EthicalFacts.option_id).
    """

    option_id: str
    """
    Identifier for the candidate option being judged.
    Must match the EthicalFacts.option_id used as input.
    """

    em_name: str
    """
    Name or identifier of the ethics module that produced this judgement,
    e.g. "case_study_1_triage" or "rights_first_compliance".
    """

    stakeholder: str
    """
    Stakeholder whose perspective this EM is intended to represent,
    e.g. "patients_and_public", "crew", "regulator", "environment".
    """

    verdict: Verdict
    """
    Categorical verdict expressing the module's normative stance:

    - "strongly_prefer": option is strongly recommended
    - "prefer": option is acceptable and preferable to neutral
    - "neutral": no strong preference for or against the option
    - "avoid": option is disfavored but not strictly forbidden
    - "forbid": option should not be chosen under this module's view
    """

    normative_score: float
    """
    Scalar measure of ethical preferability in [0.0, 1.0].

    This is suitable for aggregation (e.g., weighted voting) but SHOULD NOT
    be interpreted without the accompanying verdict and reasons.
    """

    reasons: List[str]
    """
    Human-readable explanations for the verdict and score.

    These should reference EthicalFacts dimensions (e.g., rights violations,
    unfair discrimination, high environmental harm) in a way suitable for
    audit and external review.
    """

    metadata: Dict[str, Any]
    """
    Machine-readable metadata for downstream analysis and governance.

    Examples:
    - internal weight vectors
    - flags for which constraints were triggered
    - intermediate scores by dimension (e.g., "rights_score", "env_score")
    """


# Optional convenience helpers. These are small and safe to expose.
def is_forbidden(j: EthicalJudgement) -> bool:
    """Return True if this judgement marks the option as forbidden."""
    return j.verdict == "forbid"


def is_strongly_preferred(j: EthicalJudgement) -> bool:
    """Return True if this judgement strongly prefers the option."""
    return j.verdict == "strongly_prefer"


# =============================================================================
# DEME 2.0: EthicalJudgementV2 with MoralVector
# =============================================================================


# Default weights for scalar collapse (backward compatibility)
DEFAULT_V2_WEIGHTS: Dict[str, float] = {
    "physical_harm": 1.0,
    "rights_respect": 1.0,
    "fairness_equity": 1.0,
    "autonomy_respect": 1.0,
    "legitimacy_trust": 1.0,
    "epistemic_quality": 0.5,
}


@dataclass
class EthicalJudgementV2:
    """
    DEME 2.0 judgement with MoralVector instead of scalar score.

    This is the preferred format for new code. It provides:
    - Multi-dimensional moral assessment
    - Explicit veto tracking
    - EM tier classification
    - Confidence levels
    """

    option_id: str
    """Identifier for the candidate option being judged."""

    em_name: str
    """Name of the ethics module that produced this judgement."""

    stakeholder: str
    """Stakeholder perspective this EM represents."""

    em_tier: int
    """
    Tier classification (0-4):
    - 0: Constitutional (Geneva, BasicHumanRights, NonDiscrimination)
    - 1: Core Safety (PhysicalSafety, Proxemics)
    - 2: Rights/Fairness (AutonomyConsent, AllocationFairness)
    - 3: Soft Values (Beneficence, Environmental)
    - 4: Meta-Governance (PatternGuard, ProfileIntegrity)
    """

    verdict: Verdict
    """Categorical verdict: strongly_prefer, prefer, neutral, avoid, forbid."""

    moral_vector: MoralVector
    """Multi-dimensional moral assessment replacing scalar score."""

    # V2 enhancements
    veto_triggered: bool = False
    """Whether this EM triggered a hard veto."""

    veto_reason: Optional[str] = None
    """Reason for veto if triggered."""

    confidence: float = 1.0
    """Confidence level [0, 1] in this judgement."""

    reasons: List[str] = field(default_factory=list)
    """Human-readable explanations for the verdict."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Machine-readable metadata for analysis."""

    @property
    def normative_score(self) -> float:
        """
        Collapse MoralVector to scalar for V1 compatibility.

        This enables V2 judgements to be used with V1 governance code.
        """
        return self.moral_vector.to_scalar(weights=DEFAULT_V2_WEIGHTS)

    def has_veto(self) -> bool:
        """Return True if this judgement includes a veto."""
        return self.veto_triggered or self.moral_vector.has_veto()


def is_forbidden_v2(j: EthicalJudgementV2) -> bool:
    """Return True if this V2 judgement marks the option as forbidden."""
    return j.verdict == "forbid" or j.has_veto()


def is_strongly_preferred_v2(j: EthicalJudgementV2) -> bool:
    """Return True if this V2 judgement strongly prefers the option."""
    return j.verdict == "strongly_prefer" and not j.has_veto()


# =============================================================================
# Migration Functions
# =============================================================================


def judgement_v1_to_v2(
    j: EthicalJudgement,
    em_tier: int = 2,
) -> EthicalJudgementV2:
    """
    Upgrade V1 judgement to V2 format.

    Args:
        j: The V1 EthicalJudgement.
        em_tier: Tier to assign (default 2 for Rights/Fairness).

    Returns:
        Equivalent EthicalJudgementV2.
    """
    # Import here to avoid circular import at module load
    from erisml.ethics.moral_vector import MoralVector

    # Infer moral vector from scalar score
    # This is a best-effort approximation since V1 lacks dimension breakdown
    base_score = j.normative_score

    # Check for veto
    is_veto = j.verdict == "forbid"
    veto_flags = ["V1_FORBID"] if is_veto else []

    # Create a uniform MoralVector based on the scalar score
    # For harm, we invert: higher score = lower harm
    moral_vector = MoralVector(
        physical_harm=1.0 - base_score if not is_veto else 1.0,
        rights_respect=base_score if not is_veto else 0.0,
        fairness_equity=base_score,
        autonomy_respect=base_score,
        legitimacy_trust=base_score,
        epistemic_quality=0.8,  # Default moderate confidence
        veto_flags=veto_flags,
        reason_codes=["migrated_from_v1"],
    )

    return EthicalJudgementV2(
        option_id=j.option_id,
        em_name=j.em_name,
        stakeholder=j.stakeholder,
        em_tier=em_tier,
        verdict=j.verdict,
        moral_vector=moral_vector,
        veto_triggered=is_veto,
        veto_reason="V1 forbid verdict" if is_veto else None,
        confidence=0.8,  # Lower confidence for migrated judgements
        reasons=j.reasons.copy(),
        metadata={**j.metadata, "_migrated_from_v1": True},
    )


def judgement_v2_to_v1(j: EthicalJudgementV2) -> EthicalJudgement:
    """
    Downgrade V2 judgement for V1 consumers.

    Args:
        j: The V2 EthicalJudgementV2.

    Returns:
        Equivalent V1 EthicalJudgement (with loss of dimension detail).
    """
    return EthicalJudgement(
        option_id=j.option_id,
        em_name=j.em_name,
        stakeholder=j.stakeholder,
        verdict=j.verdict,
        normative_score=j.normative_score,  # Uses property for scalar collapse
        reasons=j.reasons.copy(),
        metadata={
            **j.metadata,
            "_downgraded_from_v2": True,
            "_original_tier": j.em_tier,
            "_veto_triggered": j.veto_triggered,
        },
    )


__all__ = [
    # V1 (still supported)
    "Verdict",
    "EthicalJudgement",
    "is_forbidden",
    "is_strongly_preferred",
    # V2 (DEME 2.0)
    "EthicalJudgementV2",
    "is_forbidden_v2",
    "is_strongly_preferred_v2",
    # Migration
    "judgement_v1_to_v2",
    "judgement_v2_to_v1",
    "DEFAULT_V2_WEIGHTS",
]
