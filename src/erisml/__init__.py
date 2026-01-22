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
        VirtueAndCare,
        AutonomyAndAgency,
        PrivacyAndDataGovernance,
        TransparencyAndExplainability,
        SafetyAndSecurity,
        FairnessAndBias,
        AccountabilityAndLiability,
        SustainabilityAndEnvironment,
        SocietalAndEnvironmental,
        ProceduralAndLegitimacy,
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
    DEME = MoralTensor = EthicalFacts = EpistemicStatus = Stakeholder = None
    Timeframe = Context = Consequences = JusticeAndFairness = RightsAndDuties = None
    VirtueAndCare = AutonomyAndAgency = PrivacyAndDataGovernance = None
    TransparencyAndExplainability = SafetyAndSecurity = FairnessAndBias = None
    AccountabilityAndLiability = SustainabilityAndEnvironment = None
    SocietalAndEnvironmental = ProceduralAndLegitimacy = EthicsModule = None
    BaseEthicsModule = EthicalJudgement = None
    StrategicLayer = NashResult = CooperativeLayer = None
    GovernanceConfig = aggregate_judgements = select_option = None

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
    "VirtueAndCare",
    "AutonomyAndAgency",
    "PrivacyAndDataGovernance",
    "TransparencyAndExplainability",
    "SafetyAndSecurity",
    "FairnessAndBias",
    "AccountabilityAndLiability",
    "SustainabilityAndEnvironment",
    "SocietalAndEnvironmental",
    "ProceduralAndLegitimacy",
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
