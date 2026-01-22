"""
EthicalFacts: Core data structures for ethical reasoning.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional  # noqa: F401


@dataclass
class EpistemicStatus:
    uncertainty_level: float = 0.0
    knowledge_gaps: List[str] = field(default_factory=list)


@dataclass
class Stakeholder:
    id: str
    role: str
    impact_weight: float = 1.0


@dataclass
class Timeframe:
    duration: str = "immediate"
    urgency: float = 1.0


@dataclass
class Context:
    domain: str = "general"
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Consequences:
    short_term: Dict[str, Any] = field(default_factory=dict)
    long_term: Dict[str, Any] = field(default_factory=dict)
    probabilities: Dict[str, float] = field(default_factory=dict)


# --- V3 Paired Ethics Classes ---
@dataclass
class JusticeAndFairness:
    affected_groups: Dict[str, Any] = field(default_factory=dict)
    equity_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class RightsAndDuties:
    rights_infringed: Dict[str, Any] = field(default_factory=dict)
    duties_upheld: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VirtueAndCare:
    virtues_promoted: List[str] = field(default_factory=list)
    care_considerations: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AutonomyAndAgency:
    freedom_metrics: Dict[str, float] = field(default_factory=dict)
    informed_consent: bool = False


@dataclass
class PrivacyAndDataGovernance:
    data_usage: str = "consensual"
    retention_policy: str = "standard"


@dataclass
class TransparencyAndExplainability:
    explainability_score: float = 0.0
    transparency_level: str = "medium"


@dataclass
class SafetyAndSecurity:
    safety_protocols: List[str] = field(default_factory=list)
    risk_level: str = "low"


@dataclass
class FairnessAndBias:
    bias_metrics: Dict[str, float] = field(default_factory=dict)
    protected_groups: List[str] = field(default_factory=list)


@dataclass
class AccountabilityAndLiability:
    responsible_party: str = "user"
    audit_trail: bool = False


@dataclass
class SustainabilityAndEnvironment:
    carbon_footprint: float = 0.0
    resource_usage: float = 0.0


@dataclass
class SocietalAndEnvironmental:
    societal_impact: str = "neutral"
    environmental_impact: str = "neutral"


@dataclass
class ProceduralAndLegitimacy:
    """Specific class required by test_ethics_module_v3.py"""

    process_integrity: str = "high"
    institutional_legitimacy: str = "standard"


# --- Main Facts Class ---
@dataclass
class EthicalFacts:
    option_id: str
    scenario_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    epistemic_status: EpistemicStatus = field(default_factory=EpistemicStatus)
    stakeholders: List[Stakeholder] = field(default_factory=list)
    timeframe: Timeframe = field(default_factory=Timeframe)
    context: Context = field(default_factory=Context)
    consequences: Consequences = field(default_factory=Consequences)
    justice: JusticeAndFairness = field(default_factory=JusticeAndFairness)
    rights: RightsAndDuties = field(default_factory=RightsAndDuties)
    virtue_care: VirtueAndCare = field(default_factory=VirtueAndCare)
    autonomy: AutonomyAndAgency = field(default_factory=AutonomyAndAgency)
    privacy_gov: PrivacyAndDataGovernance = field(
        default_factory=PrivacyAndDataGovernance
    )
    transparency: TransparencyAndExplainability = field(
        default_factory=TransparencyAndExplainability
    )
    safety: SafetyAndSecurity = field(default_factory=SafetyAndSecurity)
    fairness: FairnessAndBias = field(default_factory=FairnessAndBias)
    accountability: AccountabilityAndLiability = field(
        default_factory=AccountabilityAndLiability
    )
    sustainability: SustainabilityAndEnvironment = field(
        default_factory=SustainabilityAndEnvironment
    )
    societal_env: SocietalAndEnvironmental = field(
        default_factory=SocietalAndEnvironmental
    )
    procedural: ProceduralAndLegitimacy = field(default_factory=ProceduralAndLegitimacy)
