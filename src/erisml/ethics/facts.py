"""
EthicalFacts: Core data structures for ethical reasoning.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Consequences:
    """
    Represents the predicted outcomes of an action.
    """

    short_term: Dict[str, Any] = field(default_factory=dict)
    long_term: Dict[str, Any] = field(default_factory=dict)
    probabilities: Dict[str, float] = field(default_factory=dict)


@dataclass
class EthicalFacts:
    """
    Represents the objective facts of a situation for ethical evaluation.
    """

    option_id: str
    scenario_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    consequences: Consequences = field(default_factory=Consequences)
