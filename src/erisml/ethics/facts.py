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
class EthicalFacts:
    option_id: str
    scenario_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    consequences: Consequences = field(default_factory=Consequences)
    # Dynamic fields will be added by the user manually if needed,
    # but the classes must exist for the imports to work.


@dataclass
class JusticeAndFairness:
    """Auto-generated placeholder for JusticeAndFairness"""

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RightsAndDuties:
    """Auto-generated placeholder for RightsAndDuties"""

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AutonomyAndAgency:
    """Auto-generated placeholder for AutonomyAndAgency"""

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EpistemicStatus:
    """Auto-generated placeholder for EpistemicStatus"""

    metadata: Dict[str, Any] = field(default_factory=dict)
