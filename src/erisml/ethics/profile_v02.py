# src/erisml/ethics/profile_v02.py

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


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
    How this profile resolves conflicts between principles, trustworthiness
    characteristics, and aggregate scores.

    - RIGHTS_FIRST: hard rights/privacy/fairness floors; no trade-off if violated.
    - CONSEQUENCES_FIRST: utilitarian tilt, subject to non-negotiable vetoes.
    - BALANCED_CASE_BY_CASE: no fixed lexical order; use weighted scores + vetoes.
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

    These are *normalized* (sum ~ 1.0) by tooling, but can be given in any scale.
    """

    beneficence: float = 0.25
    non_maleficence: float = 0.25
    autonomy: float = 0.25
    justice: float = 0.25


@dataclass
class TrustworthinessWeights:
    """
    Relative importance of NIST AI RMF trustworthy AI characteristics.

    See NIST AI 100-1, Section 3 (Valid & Reliable, Safe, Secure & Resilient,
    Accountable & Transparent, Explainable & Interpretable, Privacy-Enhanced,
    Fair with Harmful Bias Managed).
    """

    valid_reliable: float = 0.2
    safe: float = 0.2
    secure_resilient: float = 0.1
    accountable_transparent: float = 0.15
    explainable_interpretable: float = 0.1
    privacy_enhanced: float = 0.15
    fair_bias_managed: float = 0.1


# ---------------------------------------------------------------------------
# DEME-specific dimension weights (for EthicalFacts fields)
# ---------------------------------------------------------------------------


@dataclass
class DEMEDimensionWeights:
    """
    Weights over DEME's EthicalFacts-style dimensions.

    This ties the profile directly to what EMs actually see:
    consequences, rights & duties, justice, autonomy, privacy, social /
    environmental impact, virtue/care, procedure, epistemic status.
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
    Per-dimension tolerance for *residual* risk after controls.

    Values can be interpreted by EMs as maximum acceptable residual risk
    on [0.0, 1.0], where lower = more risk-averse / stricter threshold.
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
    """
    Overall risk posture plus per-dimension tolerances.

    This is where we connect to the NIST notion of risk as a combination of
    likelihood and magnitude of harm, and of tradeoffs between characteristics.
    """

    appetite: RiskAppetite = RiskAppetite.BALANCED
    max_overall_risk: float = 0.3  # overall maximum acceptable residual risk

    # Per-dimension tolerances (see above).
    tolerances: DimensionRiskTolerance = field(default_factory=DimensionRiskTolerance)

    # Whether to escalate (to human / governance) when risk is near limits.
    escalate_near_threshold: bool = True
    escalation_margin: float = 0.05  # within 5% of a threshold -> escalate


# ---------------------------------------------------------------------------
# Hard vetoes and policy expectations (rights, safety, content, etc.)
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
    # NEW: aligns with the YAML "never_needless_harm_to_non_human_life"
    never_needless_harm_to_non_human_life: bool = True

    # For generative AI / content-producing agents:
    never_fabricate_critical_evidence: bool = True
    never_impersonate_real_person_without_consent: bool = True


@dataclass
class GovernanceExpectations:
    """
    How the EM expects the *host organization* to behave, in a way that can be
    mapped to AI RMF GOVERN / MAP / MEASURE / MANAGE functions.
    """

    # AI RMF function coverage
    expects_govern_function: bool = True
    expects_map_function: bool = True
    expects_measure_function: bool = True
    expects_manage_function: bool = True

    # Minimum organizational practices the EM assumes are in place.
    requires_documented_risk_register: bool = True
    requires_incident_reporting_process: bool = True
    requires_human_oversight_roles_defined: bool = True
    requires_tevv_for_high_risk_use: bool = True  # Testing/Eval/Verification/Validation

    # Optional link to an organizational AI RMF profile identifier.
    ai_rmf_profile_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Pattern constraints over EthicalFacts / EthicalJudgement
# ---------------------------------------------------------------------------


@dataclass
class PatternConstraint:
    """
    A small DSL for saying things like:

    - 'FORBID_WHEN epistemic.uncertainty_level > 0.8 AND consequences.urgency < 0.3'
    - 'STRONGLY_PREFER_WHEN justice.prioritizes_most_disadvantaged == True'

    The expression language itself is up to the host system (e.g., Python
    predicates, CEL, SQL-like filters). Here we just store the abstract pattern.
    """

    name: str
    kind: PatternConstraintKind
    expression: str  # expression in a well-defined mini-language
    rationale: str  # human-readable explanation


# ---------------------------------------------------------------------------
# Main profile: DEMEProfileV02
# ---------------------------------------------------------------------------


@dataclass
class DEMEProfileV02:
    """
    DEME Profile Schema 0.1 (V02)

    This describes an *ethical stance* or *stakeholder profile* that can be
    compiled into one or more Ethics Modules (EMs). It explicitly aligns:

    - Bioethical Principlism (beneficence, non-maleficence, autonomy, justice)
    - NIST AI RMF trustworthy AI characteristics
    - DEME's EthicalFacts dimensions and veto / override logic
    """

    # ------------------------------------------------------------------
    # Identity & context
    # ------------------------------------------------------------------

    name: str
    description: str

    # Who this profile represents (e.g., "patients_and_public",
    # "Jain_community", "regulator", "hospital_ethics_committee").
    stakeholder_label: str

    # Optional context / domain where this profile applies.
    domain: Optional[str] = None  # e.g., "clinical_triage", "maritime", "GAI_content"

    version: str = "0.2.0"
    schema_version: str = "DEMEProfileV02-0.1"

    # ------------------------------------------------------------------
    # Ethically significant weightings
    # ------------------------------------------------------------------

    principlism: PrinciplismWeights = field(default_factory=PrinciplismWeights)
    trustworthiness: TrustworthinessWeights = field(
        default_factory=TrustworthinessWeights
    )
    deme_dimensions: DEMEDimensionWeights = field(default_factory=DEMEDimensionWeights)

    # ------------------------------------------------------------------
    # Risk posture & override logic
    # ------------------------------------------------------------------

    risk_attitude: RiskAttitudeProfile = field(default_factory=RiskAttitudeProfile)
    override_mode: OverrideMode = OverrideMode.BALANCED_CASE_BY_CASE

    # Optional "lexical priorities" – a mini-stack like:
    # ["rights", "safety", "fairness", "utility"]
    lexical_priority: List[str] = field(default_factory=list)

    hard_vetoes: HardVetoes = field(default_factory=HardVetoes)

    # ------------------------------------------------------------------
    # Pattern constraints and governance expectations
    # ------------------------------------------------------------------

    pattern_constraints: List[PatternConstraint] = field(default_factory=list)
    governance_expectations: GovernanceExpectations = field(
        default_factory=GovernanceExpectations
    )

    # ------------------------------------------------------------------
    # Free-form notes & tags
    # ------------------------------------------------------------------

    tags: List[str] = field(default_factory=list)
    notes: str = ""


# ---------------------------------------------------------------------------
# Helper for JSON (de-)serialization
# ---------------------------------------------------------------------------


def deme_profile_v02_to_dict(profile: DEMEProfileV02) -> Dict:
    """
    Convert a DEMEProfileV02 instance into a plain dict suitable for JSON
    serialization (e.g., to store alongside EM configuration).
    """
    from dataclasses import asdict

    data = asdict(profile)
    # Enums are serialized as their `.value`.
    data["risk_attitude"]["appetite"] = profile.risk_attitude.appetite.value
    data["override_mode"] = profile.override_mode.value
    for pc in data.get("pattern_constraints", []):
        # pattern_constraints is a list of dicts; ensure kind is serialized as value
        if "kind" in pc and isinstance(pc["kind"], Enum):
            pc["kind"] = pc["kind"].value
    return data
