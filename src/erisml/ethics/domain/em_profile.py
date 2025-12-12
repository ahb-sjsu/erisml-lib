"""
erisml.ethics.domain.em_profile
================================

Dataclasses for the DEME Ethics Module Profile, schema version 0.1.

This profile captures a stakeholder group's ethical stance in a
machine-readable format that can be consumed by ethics-only modules
operating over `EthicalFacts`.

The design is aligned with:

- Principlism in bioethics (autonomy, beneficence, nonmaleficence, justice)
- Common AI ethics principles (fairness, privacy, safety/robustness,
  transparency, accountability, sustainability)
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal


SchemaVersion = Literal["DEME-EMProfile-0.1"]

RiskAttitudeLabel = Literal["risk_averse", "balanced", "risk_seeking"]
EnergyPriority = Literal["low", "moderate", "high"]
PriorityStrength = Literal["none", "mild", "moderate", "strong"]
FairnessStrictness = Literal["none", "moderate", "strict"]
SurveillanceLevel = Literal["minimal", "contextual", "extensive"]
DataSharingMode = Literal["opt_in", "opt_out", "mandatory"]
RuleDeviationFrequency = Literal["never", "rare", "sometimes", "often"]
LogDetailLevel = Literal["minimal", "standard", "detailed"]
HumanInLoopMode = Literal["never", "high_risk_only", "always"]
OverrideMode = Literal["rights_first", "consequences_first", "balanced_case_by_case"]


@dataclass
class Provenance:
    """Provenance and process information for an EM profile."""

    collection_method: str  # e.g. "dialogue", "survey", "assembly", "mixed"
    participant_count: int
    jurisdiction: List[str] = field(default_factory=list)  # e.g. ["US-CA", "EU"]
    language: str = "en-US"


@dataclass
class Metadata:
    """Human-facing metadata and versioning details."""

    name: str
    display_name: str
    description: str
    stakeholder_group: str
    created_at: str  # ISO-8601
    updated_at: str  # ISO-8601
    version: str = "1.0.0"
    provenance: Provenance = field(
        default_factory=lambda: Provenance(
            collection_method="unknown",
            participant_count=0,
            jurisdiction=[],
            language="en-US",
        )
    )

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()


@dataclass
class PrinciplismAlignment:
    """Alignment weights for principlist bioethics."""

    autonomy: float = 0.25
    beneficence: float = 0.25
    nonmaleficence: float = 0.25
    justice: float = 0.25


@dataclass
class AIPrinciplesAlignment:
    """Alignment weights for high-level AI ethics principles."""

    fairness: float = 0.2
    privacy: float = 0.2
    safety_robustness: float = 0.2
    transparency: float = 0.2
    accountability: float = 0.1
    sustainability: float = 0.1


@dataclass
class PrincipleAlignment:
    """Aggregated alignment with principlism and AI ethics principles."""

    principlism: PrinciplismAlignment = field(default_factory=PrinciplismAlignment)
    ai_principles: AIPrinciplesAlignment = field(default_factory=AIPrinciplesAlignment)


@dataclass
class RiskAttitude:
    """Attitude toward risk and uncertainty."""

    overall: RiskAttitudeLabel = "balanced"
    harm_vs_benefit_index: float = 0.5  # 0 = benefit-seeking, 1 = very harm-averse
    epistemic_caution_index: float = 0.5  # 0 = comfortable with uncertainty


@dataclass
class SafetyPolicy:
    """Policy knobs related to safety and harm minimization."""

    min_acceptable_harm_score: float = 0.3  # max expected_harm allowed by default
    prefer_lower_risk_even_if_less_benefit: bool = True
    escalate_when_uncertainty_exceeds: float = 0.7


@dataclass
class AutonomyPolicy:
    """Policy knobs related to autonomy and consent."""

    respect_refusal_in_low_stakes: bool = True
    allow_override_in_high_stakes: bool = True
    override_requires_human_confirmation: bool = True


@dataclass
class FairnessPolicy:
    """Policy knobs related to fairness and non-discrimination."""

    avoid_protected_attr_discrimination: FairnessStrictness = "strict"
    prioritize_worse_off: PriorityStrength = "moderate"
    use_group_fairness_metrics: List[str] = field(
        default_factory=lambda: ["equal_opportunity"]
    )


@dataclass
class VulnerablePriorityPolicy:
    """Policy for prioritizing vulnerable users."""

    enabled: bool = False
    priority_strength: PriorityStrength = "mild"
    eligible_categories: List[str] = field(
        default_factory=lambda: ["children", "elderly", "disabled"]
    )


@dataclass
class PrivacyPolicy:
    """Policy for data collection, surveillance, and sharing."""

    default_surveillance: SurveillanceLevel = "contextual"
    third_party_data_sharing: DataSharingMode = "opt_in"
    data_retention_days: int = 30


@dataclass
class EnvironmentPolicy:
    """Policy for environmental and sustainability considerations."""

    energy_priority: EnergyPriority = "moderate"
    allow_high_energy_mode: bool = True
    require_explanation_for_high_energy: bool = False


@dataclass
class RuleFollowingPolicy:
    """Policy controlling adherence to formal rules and procedures."""

    follow_official_protocol_by_default: bool = True
    allow_rule_deviation_for_better_outcomes: RuleDeviationFrequency = "rare"
    deviation_requires_logging: bool = True


@dataclass
class TransparencyPolicy:
    """Policy controlling logging and explanation behavior."""

    log_decisions: LogDetailLevel = "standard"
    explanation_required_for_high_impact: bool = True


@dataclass
class OversightPolicy:
    """Policy for human oversight and escalation behavior."""

    human_in_the_loop_required: HumanInLoopMode = "high_risk_only"
    escalation_channels: List[str] = field(default_factory=list)


@dataclass
class PatternCondition:
    """
    A simple condition over an EthicalFacts field.

    Example:
        path = "rights_and_duties.violates_rights"
        op   = "=="
        value = True
    """

    path: str
    op: str
    value: Any


@dataclass
class PatternEffect:
    """
    Effect to apply when a pattern rule matches.
    """

    verdict: str  # e.g. "forbid", "avoid", "strongly_prefer"
    min_normative_score: float = 0.0
    escalation_required: bool = False


@dataclass
class PatternRule:
    """
    A rule that matches on EthicalFacts and constrains the EthicalJudgement.

    This is the main vehicle for "rights-first" or "never do X" style constraints.
    """

    id: str
    description: str
    priority: int = 0
    applies_in_domains: List[str] = field(default_factory=lambda: ["*"])

    if_all: List[PatternCondition] = field(default_factory=list)
    if_any: List[PatternCondition] = field(default_factory=list)
    unless: List[PatternCondition] = field(default_factory=list)

    effect: PatternEffect = field(
        default_factory=lambda: PatternEffect(verdict="forbid", min_normative_score=0.0)
    )

    tags: List[str] = field(default_factory=list)


@dataclass
class Constraints:
    """
    Constraint layer for the EM.

    - `hard_vetoes` are named, coarse-grained "never do this" policies.
    - `pattern_rules` are machine-executable constraints over EthicalFacts.
    """

    hard_vetoes: List[str] = field(default_factory=list)
    pattern_rules: List[PatternRule] = field(default_factory=list)


@dataclass
class OverridePolicy:
    """Policy for resolving conflicts between rights and outcomes."""

    mode: OverrideMode = "balanced_case_by_case"
    requires_human_escalation: bool = True
    document_override_reason: bool = True


@dataclass
class DEMEProfileV01:
    """
    DEME Ethics Module Profile – Schema 0.1

    This is the canonical representation of a stakeholder group's ethical stance.
    """

    schema_version: SchemaVersion = "DEME-EMProfile-0.1"
    metadata: Metadata = field(
        default_factory=lambda: Metadata(
            name="unnamed",
            display_name="Unnamed EM Profile",
            description="",
            stakeholder_group="",
            created_at=Metadata.now_iso(),
            updated_at=Metadata.now_iso(),
        )
    )

    domain_scope: List[str] = field(default_factory=list)

    principle_alignment: PrincipleAlignment = field(default_factory=PrincipleAlignment)

    # Core DEME dimensions (normalized weights).
    dimension_weights: Dict[str, float] = field(default_factory=dict)

    risk_attitude: RiskAttitude = field(default_factory=RiskAttitude)

    # Policy blocks
    safety_policy: SafetyPolicy = field(default_factory=SafetyPolicy)
    autonomy_policy: AutonomyPolicy = field(default_factory=AutonomyPolicy)
    fairness_policy: FairnessPolicy = field(default_factory=FairnessPolicy)
    vulnerable_priority_policy: VulnerablePriorityPolicy = field(
        default_factory=VulnerablePriorityPolicy
    )
    privacy_policy: PrivacyPolicy = field(default_factory=PrivacyPolicy)
    environment_policy: EnvironmentPolicy = field(default_factory=EnvironmentPolicy)
    rule_following_policy: RuleFollowingPolicy = field(
        default_factory=RuleFollowingPolicy
    )
    transparency_policy: TransparencyPolicy = field(default_factory=TransparencyPolicy)
    oversight_policy: OversightPolicy = field(default_factory=OversightPolicy)

    # Constraint layer
    constraints: Constraints = field(default_factory=Constraints)

    # How to handle rights vs consequences conflicts, at a high level.
    override_policy: OverridePolicy = field(default_factory=OverridePolicy)

    # Optional: canonical scenario responses (for auditing / refinement).
    scenario_responses: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert the profile to a plain Python dict suitable for JSON serialization."""
        return asdict(self)
