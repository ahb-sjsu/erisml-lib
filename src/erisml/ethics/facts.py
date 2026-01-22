"""
EthicalFacts: Core data structures for ethical reasoning.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional  # noqa: F401


@dataclass
class EpistemicStatus:
    """Represents certainty and knowledge state."""

    uncertainty_level: float = 0.0
    knowledge_gaps: List[str] = field(default_factory=list)


@dataclass
class Stakeholder:
    """Represents an entity affected by the decision."""

    id: str
    role: str
    impact_weight: float = 1.0


@dataclass
class Timeframe:
    """Represents temporal scope."""

    duration: str = "immediate"
    urgency: float = 1.0


@dataclass
class Context:
    """Represents situational context."""

    domain: str = "general"
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Consequences:
    short_term: Dict[str, Any] = field(default_factory=dict)
    long_term: Dict[str, Any] = field(default_factory=dict)
    probabilities: Dict[str, float] = field(default_factory=dict)


@dataclass
class JusticeAndFairness:
    affected_groups: Dict[str, Any] = field(default_factory=dict)
    equity_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class RightsAndDuties:
    rights_infringed: Dict[str, Any] = field(default_factory=dict)
    duties_upheld: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Virtues:
    virtues_promoted: Dict[str, Any] = field(default_factory=dict)
    vices_enabled: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AutonomyAndAgency:
    freedom_metrics: Dict[str, float] = field(default_factory=dict)
    informed_consent: bool = False


@dataclass
class PrivacyAndConfidentiality:
    data_sensitivity: str = "LOW"
    encryption_standard: str = "AES-256"


@dataclass
class Sustainability:
    carbon_footprint: float = 0.0
    resource_usage: float = 0.0


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
    virtues: Virtues = field(default_factory=Virtues)
    autonomy: AutonomyAndAgency = field(default_factory=AutonomyAndAgency)
    privacy: PrivacyAndConfidentiality = field(
        default_factory=PrivacyAndConfidentiality
    )
    sustainability: Sustainability = field(default_factory=Sustainability)
