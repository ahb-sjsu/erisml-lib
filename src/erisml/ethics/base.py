"""
Base classes and interfaces for Ethics Modules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any
from .facts import EthicalFacts


@dataclass
class EthicalJudgement:
    """
    The output of an ethics module evaluation.
    """

    verdict: str
    confidence: float
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
