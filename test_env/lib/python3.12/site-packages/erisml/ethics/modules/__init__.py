"""
Ethics modules (EMs) for ErisML.
"""

from .base import EthicsModule, BaseEthicsModule
from .triage_em import CaseStudy1TriageEM, RightsFirstEM
from .geneva_base_em import GenevaBaseEM, GenevaBaselineEM
from .greek_tragedy_tragic_conflict_em import TragicConflictEM  # noqa

# Registry for looking up EM implementations by identifier.
#
# NOTE:
#   - "geneva_baseline" is the canonical ID for the Geneva baseline EM.
#   - "geneva_base_em" is kept as a backwards-compatible alias that also
#     resolves to GenevaBaselineEM, so older profiles/configs continue to work.
EM_REGISTRY = {
    "case_study_1_triage": CaseStudy1TriageEM,
    "rights_first_compliance": RightsFirstEM,
    "geneva_baseline": GenevaBaselineEM,
    "geneva_base_em": GenevaBaselineEM,  # legacy alias
}

__all__ = [
    "EthicsModule",
    "BaseEthicsModule",
    "CaseStudy1TriageEM",
    "RightsFirstEM",
    "GenevaBaseEM",
    "GenevaBaselineEM",
    "EM_REGISTRY",
]
