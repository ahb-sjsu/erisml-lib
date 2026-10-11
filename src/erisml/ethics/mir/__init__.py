"""The MoralInterfaceRecord and the MIR ethics modules (docs/guides/DEME_EFM_Design_Guide_v0.1.md).

The domain layer builds a MIR; MIR ethics modules (Guide 3.1) read only the MIR; a composition
pattern (Guide 5) combines their vetoes, soft blocks and scores under a governance profile.
"""

from erisml.ethics.mir.pattern import (
    ActionVerdict,
    Level,
    MIREthicsModule,
    MIRJudgement,
    ModuleSlot,
    PatternResult,
    run_lexicographic,
)
from erisml.ethics.mir.record import (
    ActionSummary,
    ActorEffect,
    ActorSummary,
    Meta,
    MIRError,
    MoralHazardFeatures,
    MoralInterfaceRecord,
    predicates,
)

__all__ = [
    "ActionSummary",
    "ActionVerdict",
    "ActorEffect",
    "ActorSummary",
    "Level",
    "Meta",
    "MIREthicsModule",
    "MIRError",
    "MIRJudgement",
    "ModuleSlot",
    "MoralHazardFeatures",
    "MoralInterfaceRecord",
    "PatternResult",
    "predicates",
    "run_lexicographic",
]
