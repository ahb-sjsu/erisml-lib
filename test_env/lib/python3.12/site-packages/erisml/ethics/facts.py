"""
Ethically relevant facts for candidate options.

This module defines the structured "EthicalFacts" abstraction and its
component data classes. These are constructed by domain and assessment
layers, and consumed by ethics-only modules (EthicsModule).

Version: 0.2 (EthicalDomains update)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Consequences:
    """
    Consequentialist / welfare-related aspects of an option.

    All floats are expected to be in [0.0, 1.0], but this module does not
    enforce bounds at runtime; upstream assessment code is responsible for
    normalization.
    """

    expected_benefit: float
    """Estimated positive impact of this option on affected parties [0, 1]."""

    expected_harm: float
    """Estimated negative impact of this option on affected parties [0, 1]."""

    urgency: float
    """
    Time-criticality of taking this option [0, 1].

    Higher values indicate the downside of delaying this option is greater.
    """

    affected_count: int
    """Number of materially affected individuals (approximate)."""


@dataclass
class RightsAndDuties:
    """
    Rights, obligations, and rule-based constraints relevant to an option.
    """

    violates_rights: bool
    """
    True if the option would violate one or more recognized individual rights
    (e.g., bodily integrity, privacy, non-discrimination, due process).
    """

    has_valid_consent: bool
    """
    True if free and informed consent exists for the relevant intervention,
    according to applicable law and policy.
    """

    violates_explicit_rule: bool
    """
    True if the option violates an explicit rule, regulation, policy, or law
    that the system is bound to respect.
    """

    role_duty_conflict: bool
    """
    True if the option conflicts with professional or institutional duties
    (e.g., medical oaths, safety obligations, fiduciary duties).
    """


@dataclass
class JusticeAndFairness:
    """
    Distributive justice, fairness, and power-related concerns.
    """

    discriminates_on_protected_attr: bool
    """
    True if the option unjustifiably disadvantages individuals or groups on
    the basis of protected attributes (e.g., race, gender, religion).
    """

    prioritizes_most_disadvantaged: bool
    """
    True if the option gives special weight or priority to those who are
    systematically worse off (maximin / prioritarian flavor).
    """

    distributive_pattern: Optional[str] = None
    """
    High-level description of the distributive pattern, e.g.:

    - "maximin"
    - "utilitarian"
    - "egalitarian"
    - "sufficientarian"
    """

    exploits_vulnerable_population: bool = False
    """
    True if the option exploits or inappropriately burdens a vulnerable or
    dependent population (e.g., captive workers, marginalized groups).
    """

    exacerbates_power_imbalance: bool = False
    """
    True if the option meaningfully worsens an existing power imbalance
    between stakeholders (e.g., further concentrating control or dependency).
    """


@dataclass
class AutonomyAndAgency:
    """
    Autonomy and agency, beyond mere formal consent.
    """

    has_meaningful_choice: bool
    """
    True if affected parties have a genuine, practically available choice
    among alternatives (not just a nominal or highly constrained one).
    """

    coercion_or_undue_influence: bool
    """
    True if the option involves coercion, blackmail, or significant undue
    influence (e.g., economic or social pressure that undermines autonomy).
    """

    can_withdraw_without_penalty: bool
    """
    True if affected parties can withdraw or opt out without disproportionate
    penalty or retaliation.
    """

    manipulative_design_present: bool
    """
    True if the option relies on manipulative UI/UX patterns (dark patterns),
    deception, or other mechanisms that subvert reflective choice.
    """


@dataclass
class PrivacyAndDataGovernance:
    """
    Privacy, data protection, and data governance concerns.
    """

    privacy_invasion_level: float
    """
    Degree of intrusion into privacy and private life [0, 1].
    Higher values indicate more intrusive data collection or use.
    """

    data_minimization_respected: bool
    """
    True if the option adheres to data minimization (only necessary data
    are collected/used).
    """

    secondary_use_without_consent: bool
    """
    True if data are used for purposes beyond those originally consented to,
    without renewed and informed consent.
    """

    data_retention_excessive: bool
    """
    True if data are retained longer than is necessary and proportionate
    for the stated purposes.
    """

    reidentification_risk: float
    """
    Estimated risk [0, 1] that individuals can be re-identified from
    supposedly de-identified or aggregated data.
    """


@dataclass
class SocietalAndEnvironmental:
    """
    Societal, environmental, and intergenerational impacts.
    """

    environmental_harm: float
    """
    Degree of environmental harm [0, 1] (e.g., emissions, habitat damage,
    pollution) attributable to this option.
    """

    long_term_societal_risk: float
    """
    Degree of long-term risk [0, 1] the option poses to societal resilience,
    institutions, or infrastructure stability.
    """

    benefits_to_future_generations: float
    """
    Degree of benefit [0, 1] that future generations are expected to receive
    from this option (including risk reduction).
    """

    burden_on_vulnerable_groups: float
    """
    Degree [0, 1] to which the option places costs or burdens on already
    vulnerable or marginalized groups.
    """


@dataclass
class VirtueAndCare:
    """
    Virtue- and care-oriented aspects: character, trust, respect.
    """

    expresses_compassion: bool
    """
    True if the option manifests compassion or care for affected parties,
    given the context.
    """

    betrays_trust: bool
    """
    True if the option is likely to betray or erode legitimate trust
    (e.g., between patient and clinician, crew and vessel operator).
    """

    respects_person_as_end: bool
    """
    True if the option treats persons as ends in themselves (not merely as
    means), recognizing their dignity and standpoint.
    """


@dataclass
class ProceduralAndLegitimacy:
    """
    Procedural justice and legitimacy of the decision-making process.
    """

    followed_approved_procedure: bool
    """
    True if the option results from following an approved, documented
    procedure or protocol.
    """

    stakeholders_consulted: bool
    """
    True if relevant stakeholders (or their representatives) were consulted
    in the process that led to this option.
    """

    decision_explainable_to_public: bool
    """
    True if the decision behind this option can be reasonably explained to
    an informed public audience.
    """

    contestation_available: bool
    """
    True if affected parties have meaningful avenues to contest, appeal, or
    seek revision of the decision.
    """


@dataclass
class EpistemicStatus:
    """
    Epistemic quality of the assessments feeding into EthicalFacts.
    """

    uncertainty_level: float
    """
    Overall uncertainty level [0, 1] associated with the assessments used
    to construct this option's EthicalFacts. Higher means more uncertainty.
    """

    evidence_quality: str
    """
    Qualitative assessment of evidence quality, e.g.:

    - "low"
    - "medium"
    - "high"

    Implementations may restrict this to a fixed set of values.
    """

    novel_situation_flag: bool
    """
    True if the situation is significantly novel or out-of-distribution
    relative to prior experience or model training data.
    """


@dataclass
class EthicalFacts:
    """
    Ethically relevant facts for a single candidate option.

    These facts are constructed by domain- and assessment-layer components,
    and are the *only* input to ethics modules (EthicsModule). Ethics
    modules must not reach back into raw domain data, sensors, or models.
    """

    option_id: str
    """
    Identifier for the candidate option this EthicalFacts instance describes.
    Should be stable across EMs and governance.
    """

    consequences: Consequences
    rights_and_duties: RightsAndDuties
    justice_and_fairness: JusticeAndFairness

    autonomy_and_agency: Optional[AutonomyAndAgency] = None
    privacy_and_data: Optional[PrivacyAndDataGovernance] = None
    societal_and_environmental: Optional[SocietalAndEnvironmental] = None
    virtue_and_care: Optional[VirtueAndCare] = None
    procedural_and_legitimacy: Optional[ProceduralAndLegitimacy] = None
    epistemic_status: Optional[EpistemicStatus] = None

    tags: Optional[List[str]] = None
    """
    Free-form labels for logging, search, and analytics (e.g., case IDs,
    domain tags, scenario labels).
    """

    extra: Optional[Dict[str, Any]] = None
    """
    Optional dict for non-breaking extensions and domain-specific fields.

    Ethics modules should generally ignore this unless they are explicitly
    designed to use particular keys under governance control.
    """


__all__ = [
    "Consequences",
    "RightsAndDuties",
    "JusticeAndFairness",
    "AutonomyAndAgency",
    "PrivacyAndDataGovernance",
    "SocietalAndEnvironmental",
    "VirtueAndCare",
    "ProceduralAndLegitimacy",
    "EpistemicStatus",
    "EthicalFacts",
]
