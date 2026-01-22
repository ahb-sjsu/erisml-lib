__version__ = "0.1.0"

try:
    from erisml.ethics import (
        DEME,
        MoralTensor,
        Consequences,
        EthicalFacts,
        JusticeAndFairness,
        RightsAndDuties,
        AutonomyAndAgency,
        EpistemicStatus,
        EthicsModule,
        BaseEthicsModule,
        EthicalJudgement,
        StrategicLayer,
        NashResult,
        CooperativeLayer,
    )  # noqa: F401
except ImportError:
    DEME = None
    MoralTensor = None
    # Auto-generated fallbacks
    for name in [
        "Consequences",
        "EthicalFacts",
        "JusticeAndFairness",
        "RightsAndDuties",
        "AutonomyAndAgency",
        "EpistemicStatus",
    ]:
        vars()[name] = None
    EthicsModule = None
    BaseEthicsModule = None
    EthicalJudgement = None
    StrategicLayer = None
    NashResult = None
    CooperativeLayer = None

__all__ = [
    "DEME",
    "MoralTensor",
    "Consequences",
    "EthicalFacts",
    "JusticeAndFairness",
    "RightsAndDuties",
    "AutonomyAndAgency",
    "EpistemicStatus",
    "EthicsModule",
    "BaseEthicsModule",
    "EthicalJudgement",
    "StrategicLayer",
    "NashResult",
    "CooperativeLayer",
]
