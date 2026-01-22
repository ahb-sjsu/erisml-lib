"""
EthicalFacts: Core data structures for ethical reasoning.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional  # noqa: F401


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
class EthicalFacts:
    option_id: str
    scenario_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    consequences: Consequences = field(default_factory=Consequences)
    justice: JusticeAndFairness = field(default_factory=JusticeAndFairness)
    rights: RightsAndDuties = field(default_factory=RightsAndDuties)
    virtues: Virtues = field(default_factory=Virtues)
