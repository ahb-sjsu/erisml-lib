__version__ = "0.1.0"

try:
    from erisml.ethics import (
        DEME,
        MoralTensor,
        EthicalFacts,
        EpistemicStatus,
        Stakeholder,
        Timeframe,
        Context,
        Consequences,
        JusticeAndFairness,
        RightsAndDuties,
        Virtues,
        AutonomyAndAgency,
        PrivacyAndConfidentiality,
        Sustainability,
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
    # Nuclear Fallback
    DEME = None
    MoralTensor = None
    EthicalFacts = None
    EpistemicStatus = None
    Stakeholder = None
    Timeframe = None
    Context = None
    Consequences = None
    JusticeAndFairness = None
    RightsAndDuties = None
    Virtues = None
    AutonomyAndAgency = None
    PrivacyAndConfidentiality = None
    Sustainability = None
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
    "EthicalFacts",
    "EpistemicStatus",
    "Stakeholder",
    "Timeframe",
    "Context",
    "Consequences",
    "JusticeAndFairness",
    "RightsAndDuties",
    "Virtues",
    "AutonomyAndAgency",
    "PrivacyAndConfidentiality",
    "Sustainability",
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
