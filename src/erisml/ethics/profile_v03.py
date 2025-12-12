# src/erisml/ethics/profile_v03.py

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Core enums
# ---------------------------------------------------------------------------


class RiskAppetite(Enum):
    """High-level risk posture for an EM / stakeholder."""

    RISK_AVERSE = "risk_averse"
    BALANCED = "balanced"
    RISK_TOLERANT = "risk_tolerant"


class OverrideMode(Enum):
    """
    High-level summary of how this profile tends to resolve conflicts.

    The *detailed* behavior is captured by lexical_layers and override_graph,
    but this is useful for dashboards and coarse behavior.
    """

    RIGHTS_FIRST = "rights_first"
    CONSEQUENCES_FIRST = "consequences_first"
    BALANCED_CASE_BY_CASE = "balanced_case_by_case"


class PatternConstraintKind(Enum):
    """Type of pattern constraint over EthicalFacts / EthicalJudgements."""

    FORBID_WHEN = "forbid_when"
    REQUIRE_WHEN = "require_when"
    STRONGLY_PREFER_WHEN = "strongly_prefer_when"
    AVOID_WHEN = "avoid_when"


# ---------------------------------------------------------------------------
# Principlism and NIST trustworthiness weights
# ---------------------------------------------------------------------------


@dataclass
class PrinciplismWeights:
    """
    Relative importance of the four core bioethical principles.

    Values are normalized (sum ~ 1.0) by tooling, but can be specified
    in any consistent scale.
    """

    beneficence: float = 0.25
    non_maleficence: float = 0.25
    autonomy: float = 0.25
    justice: float = 0.25


@dataclass
class TrustworthinessWeights:
    """
    Relative importance of NIST AI RMF trustworthy AI characteristics.

    See NIST AI 100-1:
      - valid & reliable
      - safe
      - secure & resilient
      - accountable & transparent
      - explainable & interpretable
      - privacy-enhanced
      - fair with harmful bias managed
    """

    valid_reliable: float = 0.2
    safe: float = 0.2
    secure_resilient: float = 0.1
    accountable_transparent: float = 0.15
    explainable_interpretable: float = 0.1
    privacy_enhanced: float = 0.15
    fair_bias_managed: float = 0.1


# ---------------------------------------------------------------------------
# DEME-specific dimension weights (EthicalFacts-facing)
# ---------------------------------------------------------------------------


@dataclass
class DEMEDimensionWeights:
    """
    Weights over DEME's EthicalFacts-style dimensions.

    This is what EMs actually use when computing composite scores.
    """

    safety: float = 0.2
    autonomy_respect: float = 0.1
    fairness_equity: float = 0.2
    privacy_confidentiality: float = 0.15
    environment_societal: float = 0.1
    rule_following_legality: float = 0.1
    priority_for_vulnerable: float = 0.1
    trust_relationships: float = 0.05


# ---------------------------------------------------------------------------
# Risk attitude & thresholds
# ---------------------------------------------------------------------------


@dataclass
class DimensionRiskTolerance:
    """
    Per-dimension tolerance for residual risk after controls.

    Values in [0.0, 1.0]; lower means more risk-averse / stricter threshold.
    """

    safety: float = 0.1
    rights: float = 0.05
    fairness: float = 0.15
    privacy: float = 0.15
    information_integrity: float = 0.2
    security_resilience: float = 0.2
    environmental: float = 0.2


@dataclass
class RiskAttitudeProfile:
    """Overall risk posture plus per-dimension tolerances."""

    appetite: RiskAppetite = RiskAppetite.BALANCED
    max_overall_risk: float = 0.3  # max acceptable residual risk [0,1]

    tolerances: DimensionRiskTolerance = field(default_factory=DimensionRiskTolerance)

    escalate_near_threshold: bool = True
    escalation_margin: float = 0.05


# ---------------------------------------------------------------------------
# Hard vetoes and governance expectations
# ---------------------------------------------------------------------------


@dataclass
class HardVetoes:
    """
    Non-negotiable "red lines" – if any are triggered, the option is forbidden.
    """

    never_catastrophic_safety_harm: bool = True
    never_intentional_serious_harm: bool = True
    never_discriminate_protected_groups: bool = True
    never_violate_explicit_consent: bool = True
    never_systematic_privacy_violation: bool = True
    never_mass_surveillance_private_spaces: bool = True
    never_persistent_misinfo_disinfo_campaigns: bool = True
    never_child_sexual_abuse_or_exploitative_content: bool = True
    never_illegal_content_even_if_utility_high: bool = True
    never_needless_harm_to_non_human_life: bool = True

    # For generative/content-producing agents:
    never_fabricate_critical_evidence: bool = True
    never_impersonate_real_person_without_consent: bool = True


@dataclass
class GovernanceExpectations:
    """
    Assumptions about the deployer's governance practices, aligned with
    NIST AI RMF GOVERN / MAP / MEASURE / MANAGE.
    """

    expects_govern_function: bool = True
    expects_map_function: bool = True
    expects_measure_function: bool = True
    expects_manage_function: bool = True

    requires_documented_risk_register: bool = True
    requires_incident_reporting_process: bool = True
    requires_human_oversight_roles_defined: bool = True
    requires_tevv_for_high_risk_use: bool = True

    ai_rmf_profile_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Pattern constraints and hierarchical overrides
# ---------------------------------------------------------------------------


@dataclass
class PatternConstraint:
    """
    A small DSL for normative constraints over EthicalFacts / Judgements.

    'expression' is evaluated by the host system in some mini-language, e.g.:

      consequences.expected_harm >= 0.8
      justice_and_fairness.discriminates_on_protected_attr == true
    """

    name: str
    kind: PatternConstraintKind
    expression: str
    rationale: str


@dataclass
class LexicalLayer:
    """
    A lexical priority layer: e.g., 'rights' above 'welfare' above 'utility'.

    - name: display label
    - principles: IDs used by EMs ('rights', 'welfare', 'justice', etc.)
    - hard_stop: if True, violations at this layer cannot be overridden
    - context_condition: optional expression restricting when this layer applies
    """

    name: str
    principles: List[str]
    hard_stop: bool
    context_condition: Optional[str] = None


@dataclass
class OverrideEdge:
    """
    A directed edge in an override DAG:

      higher principle may override lower principle when context_condition holds.

    Example:
      higher='non_maleficence', lower='autonomy',
      context_condition='consequences.urgency >= 0.95 && epistemic_status.uncertainty_level <= 0.4'
    """

    higher: str
    lower: str
    context_condition: str
    strength: float = 1.0  # 0..1, how strong the trump is


# ---------------------------------------------------------------------------
# Main profile: DEMEProfileV03
# ---------------------------------------------------------------------------


@dataclass
class DEMEProfileV03:
    """
    DEME Profile Schema 0.2 (V03)

    Captures a stakeholder/community ethical stance that can be compiled into
    EMs. Aligns:

      - Principlism
      - NIST AI RMF trustworthiness characteristics
      - DEME EthicalFacts dimensions
      - Hierarchical / DAG-based override behavior
    """

    # Identity & context
    name: str
    description: str
    stakeholder_label: str
    domain: Optional[str] = None

    version: str = "0.3.0"
    schema_version: str = "DEMEProfileV03-0.1"

    # Ethically significant weightings
    principlism: PrinciplismWeights = field(default_factory=PrinciplismWeights)
    trustworthiness: TrustworthinessWeights = field(
        default_factory=TrustworthinessWeights
    )
    deme_dimensions: DEMEDimensionWeights = field(default_factory=DEMEDimensionWeights)

    # Risk posture & summary override mode
    risk_attitude: RiskAttitudeProfile = field(default_factory=RiskAttitudeProfile)
    override_mode: OverrideMode = OverrideMode.BALANCED_CASE_BY_CASE

    # Hierarchical structure
    lexical_layers: List[LexicalLayer] = field(default_factory=list)
    override_graph: List[OverrideEdge] = field(default_factory=list)

    # Constraints & governance expectations
    hard_vetoes: HardVetoes = field(default_factory=HardVetoes)
    pattern_constraints: List[PatternConstraint] = field(default_factory=list)
    governance_expectations: GovernanceExpectations = field(
        default_factory=GovernanceExpectations
    )

    # Misc
    tags: List[str] = field(default_factory=list)
    notes: str = ""


# ---------------------------------------------------------------------------
# Helpers for JSON (de-)serialization
# ---------------------------------------------------------------------------


def deme_profile_v03_to_dict(profile: DEMEProfileV03) -> Dict[str, Any]:
    """Convert a DEMEProfileV03 to a JSON-safe dict."""
    data = asdict(profile)
    # Enums → string values
    data["risk_attitude"]["appetite"] = profile.risk_attitude.appetite.value
    data["override_mode"] = profile.override_mode.value
    # pattern_constraints, lexical_layers, override_graph have no enums except kind
    for pc, orig_pc in zip(
        data.get("pattern_constraints", []), profile.pattern_constraints
    ):
        pc["kind"] = orig_pc.kind.value
    return data


def deme_profile_v03_from_dict(data: Dict[str, Any]) -> DEMEProfileV03:
    """Reconstruct a DEMEProfileV03 from a dict (e.g., JSON-loaded)."""
    ra = data.get("risk_attitude", {})
    tolerances = ra.get("tolerances", {})
    risk_attitude = RiskAttitudeProfile(
        appetite=RiskAppetite(ra.get("appetite", "balanced")),
        max_overall_risk=ra.get("max_overall_risk", 0.3),
        tolerances=DimensionRiskTolerance(**tolerances),
        escalate_near_threshold=ra.get("escalate_near_threshold", True),
        escalation_margin=ra.get("escalation_margin", 0.05),
    )

    lexical_layers = [LexicalLayer(**ll) for ll in data.get("lexical_layers", [])]

    override_graph = [OverrideEdge(**og) for og in data.get("override_graph", [])]

    pattern_constraints = [
        PatternConstraint(
            name=pc["name"],
            kind=PatternConstraintKind(pc["kind"]),
            expression=pc["expression"],
            rationale=pc["rationale"],
        )
        for pc in data.get("pattern_constraints", [])
    ]

    return DEMEProfileV03(
        name=data["name"],
        description=data.get("description", ""),
        stakeholder_label=data.get("stakeholder_label", "unspecified"),
        domain=data.get("domain"),
        version=data.get("version", "0.3.0"),
        schema_version=data.get("schema_version", "DEMEProfileV03-0.1"),
        principlism=PrinciplismWeights(**data.get("principlism", {})),
        trustworthiness=TrustworthinessWeights(**data.get("trustworthiness", {})),
        deme_dimensions=DEMEDimensionWeights(**data.get("deme_dimensions", {})),
        risk_attitude=risk_attitude,
        override_mode=OverrideMode(data.get("override_mode", "balanced_case_by_case")),
        lexical_layers=lexical_layers,
        override_graph=override_graph,
        hard_vetoes=HardVetoes(**data.get("hard_vetoes", {})),
        pattern_constraints=pattern_constraints,
        governance_expectations=GovernanceExpectations(
            **data.get("governance_expectations", {})
        ),
        tags=data.get("tags", []),
        notes=data.get("notes", ""),
    )
