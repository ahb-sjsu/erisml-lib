"""
EthicalFacts: Core data structures for ethical reasoning.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class EthicalFacts:
    """
    Represents the objective facts of a situation for ethical evaluation.
    """

    option_id: str
    scenario_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
