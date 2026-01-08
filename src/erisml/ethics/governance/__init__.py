"""
Governance layer for aggregating ethics module judgements.

Version: 2.0.0 (DEME 2.0)
"""

from .config import GovernanceConfig
from .config_v2 import GovernanceConfigV2, DimensionWeights
from .aggregation import DecisionOutcome, aggregate_judgements, select_option
from .aggregation_v2 import DecisionOutcomeV2, aggregate_moral_vectors, select_option_v2

__all__ = [
    # V1
    "GovernanceConfig",
    "DecisionOutcome",
    "aggregate_judgements",
    "select_option",
    # V2 (DEME 2.0)
    "GovernanceConfigV2",
    "DimensionWeights",
    "DecisionOutcomeV2",
    "aggregate_moral_vectors",
    "select_option_v2",
]
