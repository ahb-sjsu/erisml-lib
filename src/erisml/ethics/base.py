"""
Base classes and interfaces for Ethics Modules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from .facts import EthicalFacts


@dataclass
class EthicalJudgement:
    """
    The output of an ethics module evaluation with full test suite compliance.
    """

    verdict: str
    confidence: float = 1.0
    option_id: str = "unknown"
    em_name: str = "generic_em"
    stakeholder: str = "general"
    normative_score: float = 0.0
    reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EthicsModule(ABC):
    """
    Abstract interface for all Ethics Modules.
    """

    @abstractmethod
    def evaluate(self, facts: EthicalFacts) -> EthicalJudgement:
        pass


class BaseEthicsModule(EthicsModule):
    """
    Common base implementation for Ethics Modules.
    """

    def evaluate(self, facts: EthicalFacts) -> EthicalJudgement:
        return EthicalJudgement(verdict="ALLOW", confidence=0.5, metadata={})
