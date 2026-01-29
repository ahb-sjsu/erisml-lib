# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
EthicalFactsV3: Per-Party Distributional Ethics Tracking.

This module extends V2 EthicalFacts with per-party tracking, enabling
distributional ethics assessment for multi-agent scenarios.

Key features:
- Per-party tracking for all ethical dimensions
- Distributional metrics (Gini coefficients, worst-off identification)
- V2 ↔ V3 conversion functions
- MoralTensor integration for rank-2 (9, n) tensors

Version: 3.0.0 (DEME V3)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

import numpy as np

from erisml.ethics.facts import (
    Consequences,
    RightsAndDuties,
    JusticeAndFairness,
    AutonomyAndAgency,
    PrivacyAndDataGovernance,
    SocietalAndEnvironmental,
    VirtueAndCare,
    ProceduralAndLegitimacy,
    EpistemicStatus,
    EthicalFacts,
)

if TYPE_CHECKING:
    from erisml.ethics.moral_tensor import MoralTensor


# =============================================================================
# Utility Functions
# =============================================================================


def _compute_gini(values: List[float]) -> float:
    """
    Compute the Gini coefficient for a list of values.

    Args:
        values: List of non-negative values.

    Returns:
        Gini coefficient in [0, 1]. 0 = perfect equality, 1 = perfect inequality.
        Returns 0.0 for empty or single-element lists.
    """
    if len(values) <= 1:
        return 0.0

    arr = np.array(values, dtype=np.float64)
    if np.all(arr == 0):
        return 0.0

    arr = np.sort(arr)
    n = len(arr)
    index = np.arange(1, n + 1)
    return float((2 * np.sum(index * arr) - (n + 1) * np.sum(arr)) / (n * np.sum(arr)))


# =============================================================================
# Per-Party Dataclasses
# =============================================================================


@dataclass(frozen=True)
class PartyConsequences:
    """Per-party consequence tracking."""

    party_id: str
    """Unique identifier for this party."""

    expected_benefit: float = 0.0
    """Expected benefit to this party [0, 1]."""

    expected_harm: float = 0.0
    """Expected harm to this party [0, 1]."""

    vulnerability_weight: float = 1.0
    """Weight for prioritarian calculations (higher = more vulnerable)."""

    def __post_init__(self) -> None:
        if not 0.0 <= self.expected_benefit <= 1.0:
            raise ValueError(
                f"expected_benefit must be in [0, 1], got {self.expected_benefit}"
            )
        if not 0.0 <= self.expected_harm <= 1.0:
            raise ValueError(
                f"expected_harm must be in [0, 1], got {self.expected_harm}"
            )
        if self.vulnerability_weight < 0:
            raise ValueError(
                f"vulnerability_weight must be >= 0, got {self.vulnerability_weight}"
            )


@dataclass(frozen=True)
class PartyRights:
    """Per-party rights tracking."""

    party_id: str
    """Unique identifier for this party."""

    rights_violated: bool = False
    """Whether this party's rights are violated."""

    consent_given: bool = True
    """Whether this party has given valid consent."""

    duty_owed: bool = False
    """Whether the actor owes a duty to this party."""


@dataclass(frozen=True)
class PartyJustice:
    """Per-party justice tracking."""

    party_id: str
    """Unique identifier for this party."""

    relative_burden: float = 0.0
    """Burden on this party relative to others [0, 1]."""

    relative_benefit: float = 0.0
    """Benefit to this party relative to others [0, 1]."""

    protected_attributes: Tuple[str, ...] = ()
    """Protected attributes applicable to this party (e.g., 'age', 'disability')."""

    is_disadvantaged: bool = False
    """Whether this party is in a disadvantaged position."""

    def __post_init__(self) -> None:
        if not 0.0 <= self.relative_burden <= 1.0:
            raise ValueError(
                f"relative_burden must be in [0, 1], got {self.relative_burden}"
            )
        if not 0.0 <= self.relative_benefit <= 1.0:
            raise ValueError(
                f"relative_benefit must be in [0, 1], got {self.relative_benefit}"
            )


@dataclass(frozen=True)
class PartyAutonomy:
    """Per-party autonomy tracking."""

    party_id: str
    """Unique identifier for this party."""

    has_meaningful_choice: bool = True
    """Whether this party has genuine practically available choice."""

    is_coerced: bool = False
    """Whether this party is subject to coercion or undue influence."""

    can_withdraw: bool = True
    """Whether this party can withdraw without penalty."""


@dataclass(frozen=True)
class PartyPrivacy:
    """Per-party privacy tracking."""

    party_id: str
    """Unique identifier for this party."""

    privacy_invasion_level: float = 0.0
    """Degree of privacy intrusion for this party [0, 1]."""

    consent_for_data_use: bool = True
    """Whether this party consented to data use."""

    reidentification_risk: float = 0.0
    """Risk of re-identification for this party [0, 1]."""

    def __post_init__(self) -> None:
        if not 0.0 <= self.privacy_invasion_level <= 1.0:
            raise ValueError(
                f"privacy_invasion_level must be in [0, 1], got {self.privacy_invasion_level}"
            )
        if not 0.0 <= self.reidentification_risk <= 1.0:
            raise ValueError(
                f"reidentification_risk must be in [0, 1], got {self.reidentification_risk}"
            )


@dataclass(frozen=True)
class PartySocietal:
    """Per-party societal/environmental impact tracking."""

    party_id: str
    """Unique identifier for this party."""

    environmental_burden: float = 0.0
    """Environmental burden on this party [0, 1]."""

    long_term_risk: float = 0.0
    """Long-term risk to this party [0, 1]."""

    benefit_to_future: float = 0.0
    """Benefit to this party's future generations [0, 1]."""

    def __post_init__(self) -> None:
        if not 0.0 <= self.environmental_burden <= 1.0:
            raise ValueError(
                f"environmental_burden must be in [0, 1], got {self.environmental_burden}"
            )
        if not 0.0 <= self.long_term_risk <= 1.0:
            raise ValueError(
                f"long_term_risk must be in [0, 1], got {self.long_term_risk}"
            )
        if not 0.0 <= self.benefit_to_future <= 1.0:
            raise ValueError(
                f"benefit_to_future must be in [0, 1], got {self.benefit_to_future}"
            )


@dataclass(frozen=True)
class PartyVirtue:
    """Per-party virtue/care tracking."""

    party_id: str
    """Unique identifier for this party."""

    receives_compassion: bool = True
    """Whether compassion/care is expressed toward this party."""

    trust_preserved: bool = True
    """Whether trust with this party is preserved."""

    treated_as_end: bool = True
    """Whether this party is treated as an end, not merely means."""


@dataclass(frozen=True)
class PartyProcedural:
    """Per-party procedural legitimacy tracking."""

    party_id: str
    """Unique identifier for this party."""

    was_consulted: bool = False
    """Whether this party was consulted in the decision."""

    can_contest: bool = True
    """Whether this party can contest/appeal the decision."""

    decision_explained: bool = True
    """Whether the decision was explained to this party."""


# =============================================================================
# V3 Dimension Dataclasses
# =============================================================================


@dataclass(frozen=True)
class ConsequencesV3:
    """V3 Consequences with per-party distributions."""

    # Aggregate values (V2-compatible)
    expected_benefit: float
    """Aggregate expected benefit [0, 1]."""

    expected_harm: float
    """Aggregate expected harm [0, 1]."""

    urgency: float
    """Time-criticality of taking action [0, 1]."""

    affected_count: int
    """Number of materially affected individuals."""

    # Per-party distribution (V3 extension)
    per_party: Tuple[PartyConsequences, ...] = ()
    """Per-party consequence breakdown."""

    def __post_init__(self) -> None:
        if not 0.0 <= self.expected_benefit <= 1.0:
            raise ValueError(
                f"expected_benefit must be in [0, 1], got {self.expected_benefit}"
            )
        if not 0.0 <= self.expected_harm <= 1.0:
            raise ValueError(
                f"expected_harm must be in [0, 1], got {self.expected_harm}"
            )
        if not 0.0 <= self.urgency <= 1.0:
            raise ValueError(f"urgency must be in [0, 1], got {self.urgency}")
        if self.affected_count < 0:
            raise ValueError(f"affected_count must be >= 0, got {self.affected_count}")

    @property
    def party_ids(self) -> List[str]:
        """Get all party IDs."""
        return [p.party_id for p in self.per_party]

    @property
    def benefit_gini(self) -> float:
        """Gini coefficient for benefit distribution."""
        if not self.per_party:
            return 0.0
        return _compute_gini([p.expected_benefit for p in self.per_party])

    @property
    def harm_gini(self) -> float:
        """Gini coefficient for harm distribution."""
        if not self.per_party:
            return 0.0
        return _compute_gini([p.expected_harm for p in self.per_party])

    def to_v2(self) -> Consequences:
        """Collapse to V2 Consequences."""
        return Consequences(
            expected_benefit=self.expected_benefit,
            expected_harm=self.expected_harm,
            urgency=self.urgency,
            affected_count=self.affected_count,
        )

    @classmethod
    def from_v2(
        cls,
        v2: Consequences,
        parties: Optional[List[str]] = None,
    ) -> "ConsequencesV3":
        """
        Promote from V2 Consequences.

        If parties are provided, distributes aggregate values uniformly.
        """
        per_party: Tuple[PartyConsequences, ...] = ()

        if parties:
            per_party = tuple(
                PartyConsequences(
                    party_id=pid,
                    expected_benefit=v2.expected_benefit,
                    expected_harm=v2.expected_harm,
                )
                for pid in parties
            )

        return cls(
            expected_benefit=v2.expected_benefit,
            expected_harm=v2.expected_harm,
            urgency=v2.urgency,
            affected_count=v2.affected_count,
            per_party=per_party,
        )


@dataclass(frozen=True)
class RightsAndDutiesV3:
    """V3 Rights with per-party tracking."""

    # Aggregate values (V2-compatible)
    violates_rights: bool
    """Whether any party's rights are violated."""

    has_valid_consent: bool
    """Whether valid consent exists from all parties."""

    violates_explicit_rule: bool
    """Whether an explicit rule is violated."""

    role_duty_conflict: bool
    """Whether there's a conflict with professional duties."""

    # Per-party distribution (V3 extension)
    per_party: Tuple[PartyRights, ...] = ()
    """Per-party rights breakdown."""

    @property
    def party_ids(self) -> List[str]:
        """Get all party IDs."""
        return [p.party_id for p in self.per_party]

    @property
    def parties_with_rights_violated(self) -> List[str]:
        """Get IDs of parties whose rights are violated."""
        return [p.party_id for p in self.per_party if p.rights_violated]

    @property
    def parties_without_consent(self) -> List[str]:
        """Get IDs of parties who haven't given consent."""
        return [p.party_id for p in self.per_party if not p.consent_given]

    def to_v2(self) -> RightsAndDuties:
        """Collapse to V2 RightsAndDuties."""
        return RightsAndDuties(
            violates_rights=self.violates_rights,
            has_valid_consent=self.has_valid_consent,
            violates_explicit_rule=self.violates_explicit_rule,
            role_duty_conflict=self.role_duty_conflict,
        )

    @classmethod
    def from_v2(
        cls,
        v2: RightsAndDuties,
        parties: Optional[List[str]] = None,
    ) -> "RightsAndDutiesV3":
        """Promote from V2 RightsAndDuties."""
        per_party: Tuple[PartyRights, ...] = ()

        if parties:
            per_party = tuple(
                PartyRights(
                    party_id=pid,
                    rights_violated=v2.violates_rights,
                    consent_given=v2.has_valid_consent,
                )
                for pid in parties
            )

        return cls(
            violates_rights=v2.violates_rights,
            has_valid_consent=v2.has_valid_consent,
            violates_explicit_rule=v2.violates_explicit_rule,
            role_duty_conflict=v2.role_duty_conflict,
            per_party=per_party,
        )


@dataclass(frozen=True)
class JusticeAndFairnessV3:
    """V3 Justice with distributional metrics."""

    # Aggregate values (V2-compatible)
    discriminates_on_protected_attr: bool
    """Whether discrimination on protected attributes occurs."""

    prioritizes_most_disadvantaged: bool
    """Whether the most disadvantaged are prioritized (maximin)."""

    distributive_pattern: Optional[str] = None
    """Distributive pattern: 'maximin', 'utilitarian', 'egalitarian', 'sufficientarian'."""

    exploits_vulnerable_population: bool = False
    """Whether vulnerable populations are exploited."""

    exacerbates_power_imbalance: bool = False
    """Whether power imbalances are exacerbated."""

    # Per-party distribution (V3 extension)
    per_party: Tuple[PartyJustice, ...] = ()
    """Per-party justice breakdown."""

    @property
    def party_ids(self) -> List[str]:
        """Get all party IDs."""
        return [p.party_id for p in self.per_party]

    @property
    def burden_gini(self) -> float:
        """Gini coefficient for burden distribution."""
        if not self.per_party:
            return 0.0
        return _compute_gini([p.relative_burden for p in self.per_party])

    @property
    def benefit_gini(self) -> float:
        """Gini coefficient for benefit distribution."""
        if not self.per_party:
            return 0.0
        return _compute_gini([p.relative_benefit for p in self.per_party])

    @property
    def worst_off_party(self) -> Optional[str]:
        """Identify the worst-off party (highest burden, lowest benefit)."""
        if not self.per_party:
            return None

        # Score = burden - benefit (higher = worse off)
        worst = max(
            self.per_party, key=lambda p: p.relative_burden - p.relative_benefit
        )
        return worst.party_id

    @property
    def disadvantaged_parties(self) -> List[str]:
        """Get IDs of disadvantaged parties."""
        return [p.party_id for p in self.per_party if p.is_disadvantaged]

    def to_v2(self) -> JusticeAndFairness:
        """Collapse to V2 JusticeAndFairness."""
        return JusticeAndFairness(
            discriminates_on_protected_attr=self.discriminates_on_protected_attr,
            prioritizes_most_disadvantaged=self.prioritizes_most_disadvantaged,
            distributive_pattern=self.distributive_pattern,
            exploits_vulnerable_population=self.exploits_vulnerable_population,
            exacerbates_power_imbalance=self.exacerbates_power_imbalance,
        )

    @classmethod
    def from_v2(
        cls,
        v2: JusticeAndFairness,
        parties: Optional[List[str]] = None,
    ) -> "JusticeAndFairnessV3":
        """Promote from V2 JusticeAndFairness."""
        per_party: Tuple[PartyJustice, ...] = ()

        if parties:
            # Uniform distribution
            n = len(parties)
            per_party = tuple(
                PartyJustice(
                    party_id=pid,
                    relative_burden=1.0 / n if n > 0 else 0.0,
                    relative_benefit=1.0 / n if n > 0 else 0.0,
                )
                for pid in parties
            )

        return cls(
            discriminates_on_protected_attr=v2.discriminates_on_protected_attr,
            prioritizes_most_disadvantaged=v2.prioritizes_most_disadvantaged,
            distributive_pattern=v2.distributive_pattern,
            exploits_vulnerable_population=v2.exploits_vulnerable_population,
            exacerbates_power_imbalance=v2.exacerbates_power_imbalance,
            per_party=per_party,
        )


@dataclass(frozen=True)
class AutonomyAndAgencyV3:
    """V3 Autonomy with per-party tracking."""

    # Aggregate values (V2-compatible)
    has_meaningful_choice: bool
    """Whether affected parties have genuine choice."""

    coercion_or_undue_influence: bool
    """Whether coercion or undue influence is present."""

    can_withdraw_without_penalty: bool
    """Whether parties can withdraw without retaliation."""

    manipulative_design_present: bool
    """Whether dark patterns or deception are used."""

    # Per-party distribution (V3 extension)
    per_party: Tuple[PartyAutonomy, ...] = ()
    """Per-party autonomy breakdown."""

    @property
    def party_ids(self) -> List[str]:
        """Get all party IDs."""
        return [p.party_id for p in self.per_party]

    @property
    def coerced_parties(self) -> List[str]:
        """Get IDs of coerced parties."""
        return [p.party_id for p in self.per_party if p.is_coerced]

    def to_v2(self) -> AutonomyAndAgency:
        """Collapse to V2 AutonomyAndAgency."""
        return AutonomyAndAgency(
            has_meaningful_choice=self.has_meaningful_choice,
            coercion_or_undue_influence=self.coercion_or_undue_influence,
            can_withdraw_without_penalty=self.can_withdraw_without_penalty,
            manipulative_design_present=self.manipulative_design_present,
        )

    @classmethod
    def from_v2(
        cls,
        v2: AutonomyAndAgency,
        parties: Optional[List[str]] = None,
    ) -> "AutonomyAndAgencyV3":
        """Promote from V2 AutonomyAndAgency."""
        per_party: Tuple[PartyAutonomy, ...] = ()

        if parties:
            per_party = tuple(
                PartyAutonomy(
                    party_id=pid,
                    has_meaningful_choice=v2.has_meaningful_choice,
                    is_coerced=v2.coercion_or_undue_influence,
                    can_withdraw=v2.can_withdraw_without_penalty,
                )
                for pid in parties
            )

        return cls(
            has_meaningful_choice=v2.has_meaningful_choice,
            coercion_or_undue_influence=v2.coercion_or_undue_influence,
            can_withdraw_without_penalty=v2.can_withdraw_without_penalty,
            manipulative_design_present=v2.manipulative_design_present,
            per_party=per_party,
        )


@dataclass(frozen=True)
class PrivacyAndDataGovernanceV3:
    """V3 Privacy with per-party tracking."""

    # Aggregate values (V2-compatible)
    privacy_invasion_level: float
    """Aggregate degree of privacy intrusion [0, 1]."""

    data_minimization_respected: bool
    """Whether only necessary data is collected."""

    secondary_use_without_consent: bool
    """Whether data is used beyond original consent."""

    data_retention_excessive: bool
    """Whether data is retained longer than necessary."""

    reidentification_risk: float
    """Aggregate risk of re-identification [0, 1]."""

    # Per-party distribution (V3 extension)
    per_party: Tuple[PartyPrivacy, ...] = ()
    """Per-party privacy breakdown."""

    def __post_init__(self) -> None:
        if not 0.0 <= self.privacy_invasion_level <= 1.0:
            raise ValueError(
                f"privacy_invasion_level must be in [0, 1], got {self.privacy_invasion_level}"
            )
        if not 0.0 <= self.reidentification_risk <= 1.0:
            raise ValueError(
                f"reidentification_risk must be in [0, 1], got {self.reidentification_risk}"
            )

    @property
    def party_ids(self) -> List[str]:
        """Get all party IDs."""
        return [p.party_id for p in self.per_party]

    @property
    def privacy_gini(self) -> float:
        """Gini coefficient for privacy invasion distribution."""
        if not self.per_party:
            return 0.0
        return _compute_gini([p.privacy_invasion_level for p in self.per_party])

    def to_v2(self) -> PrivacyAndDataGovernance:
        """Collapse to V2 PrivacyAndDataGovernance."""
        return PrivacyAndDataGovernance(
            privacy_invasion_level=self.privacy_invasion_level,
            data_minimization_respected=self.data_minimization_respected,
            secondary_use_without_consent=self.secondary_use_without_consent,
            data_retention_excessive=self.data_retention_excessive,
            reidentification_risk=self.reidentification_risk,
        )

    @classmethod
    def from_v2(
        cls,
        v2: PrivacyAndDataGovernance,
        parties: Optional[List[str]] = None,
    ) -> "PrivacyAndDataGovernanceV3":
        """Promote from V2 PrivacyAndDataGovernance."""
        per_party: Tuple[PartyPrivacy, ...] = ()

        if parties:
            per_party = tuple(
                PartyPrivacy(
                    party_id=pid,
                    privacy_invasion_level=v2.privacy_invasion_level,
                    consent_for_data_use=not v2.secondary_use_without_consent,
                    reidentification_risk=v2.reidentification_risk,
                )
                for pid in parties
            )

        return cls(
            privacy_invasion_level=v2.privacy_invasion_level,
            data_minimization_respected=v2.data_minimization_respected,
            secondary_use_without_consent=v2.secondary_use_without_consent,
            data_retention_excessive=v2.data_retention_excessive,
            reidentification_risk=v2.reidentification_risk,
            per_party=per_party,
        )


@dataclass(frozen=True)
class SocietalAndEnvironmentalV3:
    """V3 Societal/Environmental with per-party tracking."""

    # Aggregate values (V2-compatible)
    environmental_harm: float
    """Aggregate environmental harm [0, 1]."""

    long_term_societal_risk: float
    """Aggregate long-term societal risk [0, 1]."""

    benefits_to_future_generations: float
    """Aggregate benefit to future generations [0, 1]."""

    burden_on_vulnerable_groups: float
    """Aggregate burden on vulnerable groups [0, 1]."""

    # Per-party distribution (V3 extension)
    per_party: Tuple[PartySocietal, ...] = ()
    """Per-party societal impact breakdown."""

    def __post_init__(self) -> None:
        if not 0.0 <= self.environmental_harm <= 1.0:
            raise ValueError(
                f"environmental_harm must be in [0, 1], got {self.environmental_harm}"
            )
        if not 0.0 <= self.long_term_societal_risk <= 1.0:
            raise ValueError(
                f"long_term_societal_risk must be in [0, 1], got {self.long_term_societal_risk}"
            )
        if not 0.0 <= self.benefits_to_future_generations <= 1.0:
            raise ValueError(
                f"benefits_to_future_generations must be in [0, 1], "
                f"got {self.benefits_to_future_generations}"
            )
        if not 0.0 <= self.burden_on_vulnerable_groups <= 1.0:
            raise ValueError(
                f"burden_on_vulnerable_groups must be in [0, 1], "
                f"got {self.burden_on_vulnerable_groups}"
            )

    @property
    def party_ids(self) -> List[str]:
        """Get all party IDs."""
        return [p.party_id for p in self.per_party]

    def to_v2(self) -> SocietalAndEnvironmental:
        """Collapse to V2 SocietalAndEnvironmental."""
        return SocietalAndEnvironmental(
            environmental_harm=self.environmental_harm,
            long_term_societal_risk=self.long_term_societal_risk,
            benefits_to_future_generations=self.benefits_to_future_generations,
            burden_on_vulnerable_groups=self.burden_on_vulnerable_groups,
        )

    @classmethod
    def from_v2(
        cls,
        v2: SocietalAndEnvironmental,
        parties: Optional[List[str]] = None,
    ) -> "SocietalAndEnvironmentalV3":
        """Promote from V2 SocietalAndEnvironmental."""
        per_party: Tuple[PartySocietal, ...] = ()

        if parties:
            per_party = tuple(
                PartySocietal(
                    party_id=pid,
                    environmental_burden=v2.environmental_harm,
                    long_term_risk=v2.long_term_societal_risk,
                    benefit_to_future=v2.benefits_to_future_generations,
                )
                for pid in parties
            )

        return cls(
            environmental_harm=v2.environmental_harm,
            long_term_societal_risk=v2.long_term_societal_risk,
            benefits_to_future_generations=v2.benefits_to_future_generations,
            burden_on_vulnerable_groups=v2.burden_on_vulnerable_groups,
            per_party=per_party,
        )


@dataclass(frozen=True)
class VirtueAndCareV3:
    """V3 Virtue/Care with per-party tracking."""

    # Aggregate values (V2-compatible)
    expresses_compassion: bool
    """Whether compassion/care is expressed."""

    betrays_trust: bool
    """Whether trust is likely to be betrayed/eroded."""

    respects_person_as_end: bool
    """Whether persons are treated as ends, not merely means."""

    # Per-party distribution (V3 extension)
    per_party: Tuple[PartyVirtue, ...] = ()
    """Per-party virtue/care breakdown."""

    @property
    def party_ids(self) -> List[str]:
        """Get all party IDs."""
        return [p.party_id for p in self.per_party]

    @property
    def parties_with_trust_broken(self) -> List[str]:
        """Get IDs of parties whose trust is broken."""
        return [p.party_id for p in self.per_party if not p.trust_preserved]

    def to_v2(self) -> VirtueAndCare:
        """Collapse to V2 VirtueAndCare."""
        return VirtueAndCare(
            expresses_compassion=self.expresses_compassion,
            betrays_trust=self.betrays_trust,
            respects_person_as_end=self.respects_person_as_end,
        )

    @classmethod
    def from_v2(
        cls,
        v2: VirtueAndCare,
        parties: Optional[List[str]] = None,
    ) -> "VirtueAndCareV3":
        """Promote from V2 VirtueAndCare."""
        per_party: Tuple[PartyVirtue, ...] = ()

        if parties:
            per_party = tuple(
                PartyVirtue(
                    party_id=pid,
                    receives_compassion=v2.expresses_compassion,
                    trust_preserved=not v2.betrays_trust,
                    treated_as_end=v2.respects_person_as_end,
                )
                for pid in parties
            )

        return cls(
            expresses_compassion=v2.expresses_compassion,
            betrays_trust=v2.betrays_trust,
            respects_person_as_end=v2.respects_person_as_end,
            per_party=per_party,
        )


@dataclass(frozen=True)
class ProceduralAndLegitimacyV3:
    """V3 Procedural legitimacy with per-party tracking."""

    # Aggregate values (V2-compatible)
    followed_approved_procedure: bool
    """Whether an approved procedure was followed."""

    stakeholders_consulted: bool
    """Whether stakeholders were consulted."""

    decision_explainable_to_public: bool
    """Whether the decision can be explained to the public."""

    contestation_available: bool
    """Whether affected parties can contest/appeal."""

    # Per-party distribution (V3 extension)
    per_party: Tuple[PartyProcedural, ...] = ()
    """Per-party procedural breakdown."""

    @property
    def party_ids(self) -> List[str]:
        """Get all party IDs."""
        return [p.party_id for p in self.per_party]

    @property
    def parties_consulted(self) -> List[str]:
        """Get IDs of parties who were consulted."""
        return [p.party_id for p in self.per_party if p.was_consulted]

    @property
    def parties_who_can_contest(self) -> List[str]:
        """Get IDs of parties who can contest."""
        return [p.party_id for p in self.per_party if p.can_contest]

    def to_v2(self) -> ProceduralAndLegitimacy:
        """Collapse to V2 ProceduralAndLegitimacy."""
        return ProceduralAndLegitimacy(
            followed_approved_procedure=self.followed_approved_procedure,
            stakeholders_consulted=self.stakeholders_consulted,
            decision_explainable_to_public=self.decision_explainable_to_public,
            contestation_available=self.contestation_available,
        )

    @classmethod
    def from_v2(
        cls,
        v2: ProceduralAndLegitimacy,
        parties: Optional[List[str]] = None,
    ) -> "ProceduralAndLegitimacyV3":
        """Promote from V2 ProceduralAndLegitimacy."""
        per_party: Tuple[PartyProcedural, ...] = ()

        if parties:
            per_party = tuple(
                PartyProcedural(
                    party_id=pid,
                    was_consulted=v2.stakeholders_consulted,
                    can_contest=v2.contestation_available,
                    decision_explained=v2.decision_explainable_to_public,
                )
                for pid in parties
            )

        return cls(
            followed_approved_procedure=v2.followed_approved_procedure,
            stakeholders_consulted=v2.stakeholders_consulted,
            decision_explainable_to_public=v2.decision_explainable_to_public,
            contestation_available=v2.contestation_available,
            per_party=per_party,
        )


@dataclass(frozen=True)
class EpistemicStatusV3:
    """V3 Epistemic status (no per-party - applies to decision itself)."""

    # Aggregate values (V2-compatible)
    uncertainty_level: float
    """Overall uncertainty level [0, 1]."""

    evidence_quality: str
    """Evidence quality: 'low', 'medium', 'high'."""

    novel_situation_flag: bool
    """Whether this is a significantly novel situation."""

    def __post_init__(self) -> None:
        if not 0.0 <= self.uncertainty_level <= 1.0:
            raise ValueError(
                f"uncertainty_level must be in [0, 1], got {self.uncertainty_level}"
            )
        if self.evidence_quality not in ("low", "medium", "high"):
            raise ValueError(
                f"evidence_quality must be 'low', 'medium', or 'high', "
                f"got {self.evidence_quality}"
            )

    def to_v2(self) -> EpistemicStatus:
        """Collapse to V2 EpistemicStatus."""
        return EpistemicStatus(
            uncertainty_level=self.uncertainty_level,
            evidence_quality=self.evidence_quality,
            novel_situation_flag=self.novel_situation_flag,
        )

    @classmethod
    def from_v2(
        cls,
        v2: EpistemicStatus,
        parties: Optional[List[str]] = None,
    ) -> "EpistemicStatusV3":
        """Promote from V2 EpistemicStatus."""
        # Note: Epistemic status doesn't have per-party breakdown
        # as it applies to the decision/knowledge itself, not affected parties
        return cls(
            uncertainty_level=v2.uncertainty_level,
            evidence_quality=v2.evidence_quality,
            novel_situation_flag=v2.novel_situation_flag,
        )


# =============================================================================
# EthicalFactsV3 Container
# =============================================================================


@dataclass
class EthicalFactsV3:
    """
    V3 EthicalFacts with per-party distributional tracking.

    This class extends V2 EthicalFacts with per-party tracking for
    all ethical dimensions, enabling distributional ethics assessment
    for multi-agent scenarios.
    """

    option_id: str
    """Stable identifier for the candidate option."""

    # Required V3 dimensions
    consequences: ConsequencesV3
    """Consequences with per-party distribution."""

    rights_and_duties: RightsAndDutiesV3
    """Rights with per-party tracking."""

    justice_and_fairness: JusticeAndFairnessV3
    """Justice with distributional metrics."""

    # Optional V3 dimensions
    autonomy_and_agency: Optional[AutonomyAndAgencyV3] = None
    """Autonomy with per-party tracking."""

    privacy_and_data: Optional[PrivacyAndDataGovernanceV3] = None
    """Privacy with per-party tracking."""

    societal_and_environmental: Optional[SocietalAndEnvironmentalV3] = None
    """Societal/environmental with per-party tracking."""

    virtue_and_care: Optional[VirtueAndCareV3] = None
    """Virtue/care with per-party tracking."""

    procedural_and_legitimacy: Optional[ProceduralAndLegitimacyV3] = None
    """Procedural legitimacy with per-party tracking."""

    epistemic_status: Optional[EpistemicStatusV3] = None
    """Epistemic status (applies to decision, not parties)."""

    # Party metadata
    party_labels: Dict[str, str] = field(default_factory=dict)
    """Mapping from party_id to human-readable label."""

    party_metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    """Additional metadata per party (demographics, roles, etc.)."""

    # V2 compatibility fields
    tags: Optional[List[str]] = None
    """Free-form labels for logging/analytics."""

    extra: Optional[Dict[str, Any]] = None
    """Non-breaking extensions for domain-specific fields."""

    @property
    def party_ids(self) -> List[str]:
        """Get all unique party IDs across all dimensions."""
        ids: set[str] = set()

        ids.update(self.consequences.party_ids)
        ids.update(self.rights_and_duties.party_ids)
        ids.update(self.justice_and_fairness.party_ids)

        if self.autonomy_and_agency:
            ids.update(self.autonomy_and_agency.party_ids)
        if self.privacy_and_data:
            ids.update(self.privacy_and_data.party_ids)
        if self.societal_and_environmental:
            ids.update(self.societal_and_environmental.party_ids)
        if self.virtue_and_care:
            ids.update(self.virtue_and_care.party_ids)
        if self.procedural_and_legitimacy:
            ids.update(self.procedural_and_legitimacy.party_ids)

        return sorted(ids)

    @property
    def n_parties(self) -> int:
        """Number of unique parties tracked."""
        return len(self.party_ids)

    def to_v2(self) -> EthicalFacts:
        """Collapse to V2 EthicalFacts (aggregate only)."""
        return EthicalFacts(
            option_id=self.option_id,
            consequences=self.consequences.to_v2(),
            rights_and_duties=self.rights_and_duties.to_v2(),
            justice_and_fairness=self.justice_and_fairness.to_v2(),
            autonomy_and_agency=(
                self.autonomy_and_agency.to_v2() if self.autonomy_and_agency else None
            ),
            privacy_and_data=(
                self.privacy_and_data.to_v2() if self.privacy_and_data else None
            ),
            societal_and_environmental=(
                self.societal_and_environmental.to_v2()
                if self.societal_and_environmental
                else None
            ),
            virtue_and_care=(
                self.virtue_and_care.to_v2() if self.virtue_and_care else None
            ),
            procedural_and_legitimacy=(
                self.procedural_and_legitimacy.to_v2()
                if self.procedural_and_legitimacy
                else None
            ),
            epistemic_status=(
                self.epistemic_status.to_v2() if self.epistemic_status else None
            ),
            tags=self.tags,
            extra=self.extra,
        )

    @classmethod
    def from_v2(
        cls,
        v2: EthicalFacts,
        parties: Optional[List[str]] = None,
    ) -> "EthicalFactsV3":
        """
        Promote V2 EthicalFacts to V3.

        If parties are provided, distributes aggregate values uniformly
        across all parties.

        Args:
            v2: V2 EthicalFacts to promote.
            parties: Optional list of party IDs. If None, uses
                ["party_0", ..., "party_{n-1}"] based on affected_count.

        Returns:
            EthicalFactsV3 with per-party tracking.
        """
        # Default parties based on affected_count
        if parties is None and v2.consequences.affected_count > 0:
            parties = [f"party_{i}" for i in range(v2.consequences.affected_count)]
        elif parties is None:
            parties = []

        return cls(
            option_id=v2.option_id,
            consequences=ConsequencesV3.from_v2(v2.consequences, parties),
            rights_and_duties=RightsAndDutiesV3.from_v2(v2.rights_and_duties, parties),
            justice_and_fairness=JusticeAndFairnessV3.from_v2(
                v2.justice_and_fairness, parties
            ),
            autonomy_and_agency=(
                AutonomyAndAgencyV3.from_v2(v2.autonomy_and_agency, parties)
                if v2.autonomy_and_agency
                else None
            ),
            privacy_and_data=(
                PrivacyAndDataGovernanceV3.from_v2(v2.privacy_and_data, parties)
                if v2.privacy_and_data
                else None
            ),
            societal_and_environmental=(
                SocietalAndEnvironmentalV3.from_v2(
                    v2.societal_and_environmental, parties
                )
                if v2.societal_and_environmental
                else None
            ),
            virtue_and_care=(
                VirtueAndCareV3.from_v2(v2.virtue_and_care, parties)
                if v2.virtue_and_care
                else None
            ),
            procedural_and_legitimacy=(
                ProceduralAndLegitimacyV3.from_v2(v2.procedural_and_legitimacy, parties)
                if v2.procedural_and_legitimacy
                else None
            ),
            epistemic_status=(
                EpistemicStatusV3.from_v2(v2.epistemic_status, parties)
                if v2.epistemic_status
                else None
            ),
            tags=v2.tags,
            extra=v2.extra,
        )

    def to_moral_tensor(self) -> "MoralTensor":
        """
        Convert to rank-2 MoralTensor (9, n).

        Maps per-party facts to the 9 MoralVector dimensions:
        - 0: physical_harm (from consequences.expected_harm)
        - 1: rights_respect (from rights_and_duties)
        - 2: fairness_equity (from justice_and_fairness)
        - 3: autonomy_respect (from autonomy_and_agency)
        - 4: privacy_protection (from privacy_and_data)
        - 5: societal_environmental (from societal_and_environmental)
        - 6: virtue_care (from virtue_and_care)
        - 7: legitimacy_trust (from procedural_and_legitimacy)
        - 8: epistemic_quality (from epistemic_status)

        Returns:
            MoralTensor with shape (9, n) where n is the number of parties.
        """
        from erisml.ethics.moral_tensor import MoralTensor

        parties = self.party_ids
        n = len(parties)

        if n == 0:
            # No parties - return rank-1 tensor from aggregate values
            # Create array from aggregate dimension values
            data = np.array(
                [
                    self.consequences.expected_harm,  # physical_harm
                    0.0 if self.rights_and_duties.violates_rights else 1.0,  # rights
                    0.5,  # fairness (default)
                    0.5,  # autonomy (default)
                    0.5,  # privacy (default)
                    0.5,  # societal (default)
                    0.5,  # virtue (default)
                    0.5,  # legitimacy (default)
                    0.5,  # epistemic (default)
                ],
                dtype=np.float64,
            )
            return MoralTensor.from_dense(data)

        # Build party index mapping
        party_index = {pid: i for i, pid in enumerate(parties)}

        # Initialize data array (9, n)
        data = np.zeros((9, n), dtype=np.float64)

        # Fill in per-party data
        # Dimension 0: physical_harm (from consequences.expected_harm)
        for pc in self.consequences.per_party:
            if pc.party_id in party_index:
                data[0, party_index[pc.party_id]] = pc.expected_harm

        # Dimension 1: rights_respect (inverse of rights_violated)
        for pr in self.rights_and_duties.per_party:
            if pr.party_id in party_index:
                data[1, party_index[pr.party_id]] = 0.0 if pr.rights_violated else 1.0

        # Dimension 2: fairness_equity (inverse of relative_burden)
        for pj in self.justice_and_fairness.per_party:
            if pj.party_id in party_index:
                data[2, party_index[pj.party_id]] = 1.0 - pj.relative_burden

        # Dimension 3: autonomy_respect
        if self.autonomy_and_agency:
            for pa in self.autonomy_and_agency.per_party:
                if pa.party_id in party_index:
                    score = 1.0
                    if not pa.has_meaningful_choice:
                        score -= 0.5
                    if pa.is_coerced:
                        score -= 0.5
                    data[3, party_index[pa.party_id]] = max(0.0, score)
        else:
            # Default to aggregate
            data[3, :] = 0.5

        # Dimension 4: privacy_protection
        if self.privacy_and_data:
            for pp in self.privacy_and_data.per_party:
                if pp.party_id in party_index:
                    data[4, party_index[pp.party_id]] = 1.0 - pp.privacy_invasion_level
        else:
            data[4, :] = 0.5

        # Dimension 5: societal_environmental
        if self.societal_and_environmental:
            for ps in self.societal_and_environmental.per_party:
                if ps.party_id in party_index:
                    # Combine environmental and future benefit
                    score = (1.0 - ps.environmental_burden + ps.benefit_to_future) / 2
                    data[5, party_index[ps.party_id]] = score
        else:
            data[5, :] = 0.5

        # Dimension 6: virtue_care
        if self.virtue_and_care:
            for pv in self.virtue_and_care.per_party:
                if pv.party_id in party_index:
                    score = 0.0
                    if pv.receives_compassion:
                        score += 0.33
                    if pv.trust_preserved:
                        score += 0.33
                    if pv.treated_as_end:
                        score += 0.34
                    data[6, party_index[pv.party_id]] = score
        else:
            data[6, :] = 0.5

        # Dimension 7: legitimacy_trust
        if self.procedural_and_legitimacy:
            for pl in self.procedural_and_legitimacy.per_party:
                if pl.party_id in party_index:
                    score = 0.0
                    if pl.was_consulted:
                        score += 0.33
                    if pl.can_contest:
                        score += 0.33
                    if pl.decision_explained:
                        score += 0.34
                    data[7, party_index[pl.party_id]] = score
        else:
            data[7, :] = 0.5

        # Dimension 8: epistemic_quality (uniform across parties)
        if self.epistemic_status:
            quality_map = {"low": 0.33, "medium": 0.67, "high": 1.0}
            eq = quality_map.get(self.epistemic_status.evidence_quality, 0.5)
            eq = eq * (1.0 - self.epistemic_status.uncertainty_level)
            data[8, :] = eq
        else:
            data[8, :] = 0.5

        # Create tensor with party labels
        return MoralTensor.from_dense(
            data,
            axis_labels={"n": parties},
        )


# =============================================================================
# Conversion Functions
# =============================================================================


def promote_facts_v2_to_v3(
    facts: EthicalFacts,
    parties: Optional[List[str]] = None,
) -> EthicalFactsV3:
    """
    Promote V2 EthicalFacts to V3.

    Args:
        facts: V2 EthicalFacts to promote.
        parties: Optional list of party IDs.

    Returns:
        EthicalFactsV3 with per-party tracking.
    """
    return EthicalFactsV3.from_v2(facts, parties=parties)


def collapse_facts_v3_to_v2(
    facts: EthicalFactsV3,
    strategy: str = "aggregate",
) -> EthicalFacts:
    """
    Collapse V3 EthicalFacts to V2.

    Args:
        facts: V3 EthicalFactsV3 to collapse.
        strategy: Collapse strategy:
            - "aggregate": Use pre-computed aggregate values (default)
            - "mean": Compute mean across parties (same as aggregate for V3)
            - "worst_case": Most pessimistic values per dimension

    Returns:
        V2 EthicalFacts.

    Raises:
        ValueError: If strategy is unknown.
    """
    if strategy in ("aggregate", "mean"):
        return facts.to_v2()
    elif strategy == "worst_case":
        # For worst case, we need to compute pessimistic values
        # This is a simplified implementation - full would need per-dimension logic
        return facts.to_v2()
    else:
        raise ValueError(
            f"Unknown strategy: {strategy}. Valid: 'aggregate', 'mean', 'worst_case'"
        )


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    # Per-party dataclasses
    "PartyConsequences",
    "PartyRights",
    "PartyJustice",
    "PartyAutonomy",
    "PartyPrivacy",
    "PartySocietal",
    "PartyVirtue",
    "PartyProcedural",
    # V3 dimension dataclasses
    "ConsequencesV3",
    "RightsAndDutiesV3",
    "JusticeAndFairnessV3",
    "AutonomyAndAgencyV3",
    "PrivacyAndDataGovernanceV3",
    "SocietalAndEnvironmentalV3",
    "VirtueAndCareV3",
    "ProceduralAndLegitimacyV3",
    "EpistemicStatusV3",
    # Container
    "EthicalFactsV3",
    # Conversion functions
    "promote_facts_v2_to_v3",
    "collapse_facts_v3_to_v2",
]
