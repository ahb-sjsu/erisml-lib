"""
EthicalFacts: Core data structures for ethical reasoning.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class Consequences:
    """
    Represents the predicted outcomes of an action.
    """

    short_term: Dict[str, Any] = field(default_factory=dict)
    long_term: Dict[str, Any] = field(default_factory=dict)
    probabilities: Dict[str, float] = field(default_factory=dict)


@dataclass
class JusticeAndFairness:
    """
    Represents justice and fairness considerations.
    """

    affected_groups: Dict[str, Any] = field(default_factory=dict)
    equity_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class RightsAndDuties:
    """
    Represents rights violations or duty fulfillments.
    """

    rights_infringed: Dict[str, Any] = field(default_factory=dict)
    duties_upheld: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Virtues:
    """
    Represents character virtues or vices implicated.
    """

    virtues_promoted: Dict[str, Any] = field(default_factory=dict)
    vices_enabled: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EthicalFacts:
    """
    Represents the objective facts of a situation for ethical evaluation.
    """

    option_id: str
    scenario_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    consequences: Consequences = field(default_factory=Consequences)
    justice: JusticeAndFairness = field(default_factory=JusticeAndFairness)
    rights: RightsAndDuties = field(default_factory=RightsAndDuties)
    virtues: Virtues = field(default_factory=Virtues)
