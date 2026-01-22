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
    
        GovernanceConfig,
        aggregate_judgements,
        select_option,
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
        "GovernanceConfig",
    "aggregate_judgements",
    "select_option",
]:
        vars()[name    "GovernanceConfig",
    "aggregate_judgements",
    "select_option",
] = None
    EthicsModule = None
    BaseEthicsModule = None
    EthicalJudgement = None
    StrategicLayer = None
    NashResult = None
    CooperativeLayer = None
    GovernanceConfig = None
    aggregate_judgements = None
    select_option = None


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
    "GovernanceConfig",
    "aggregate_judgements",
    "select_option",
]
