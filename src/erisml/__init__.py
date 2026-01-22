__version__ = "0.1.0"

try:
    from erisml.ethics import (
        DEME,
        MoralTensor,
        EthicalFacts,
        Consequences,
        JusticeAndFairness,
        RightsAndDuties,
        Virtues,
        EthicsModule,
        BaseEthicsModule,
        EthicalJudgement,
        StrategicLayer,
        NashResult,
        CooperativeLayer,
    )  # noqa: F401
except ImportError:
    # Fallback to avoid setup.py crashing
    DEME = None
    MoralTensor = None
    EthicalFacts = None
    Consequences = None
    JusticeAndFairness = None
    RightsAndDuties = None
    Virtues = None
    EthicsModule = None
    BaseEthicsModule = None
    EthicalJudgement = None
    StrategicLayer = None
    NashResult = None
    CooperativeLayer = None

__all__ = [
    "DEME",
    "MoralTensor",
    "EthicalFacts",
    "Consequences",
    "JusticeAndFairness",
    "RightsAndDuties",
    "Virtues",
    "EthicsModule",
    "BaseEthicsModule",
    "EthicalJudgement",
    "StrategicLayer",
    "NashResult",
    "CooperativeLayer",
]
