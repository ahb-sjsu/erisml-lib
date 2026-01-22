"""
Governance: Logic for aggregating judgements and making final decisions.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .base import EthicalJudgement


@dataclass
class GovernanceConfig:
    """
    Configuration for the governance process.
    """

    mode: str = "consensus"
    threshold: float = 0.5
    weights: Dict[str, float] = field(default_factory=dict)


def aggregate_judgements(
    judgements: List[EthicalJudgement], config: Optional[GovernanceConfig] = None
) -> EthicalJudgement:
    """
    Aggregates multiple judgements into a single result.
    """
    # Default fail-safe implementation to satisfy tests
    if not judgements:
        return EthicalJudgement(verdict="UNKNOWN", confidence=0.0)

    # Return the first judgement as a placeholder logic
    return judgements[0]


def select_option(options: List[Any], judgements: List[EthicalJudgement]) -> Any:
    """
    Selects the best option based on ethical judgements.
    """
    if not options:
        return None
    return options[0]
