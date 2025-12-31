"""
Governance layer for aggregating ethics module judgements.
"""

from .config import GovernanceConfig
from .aggregation import DecisionOutcome, aggregate_judgements, select_option

__all__ = [
    "GovernanceConfig",
    "DecisionOutcome",
    "aggregate_judgements",
    "select_option",
]
