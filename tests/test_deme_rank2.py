"""DEME at rank 2: each module judges each party's view of each option.

Before, DEMEPipeline ran every module on one aggregate EthicalFacts record per option, a rank-1
MoralVector of nine dimensions, although DEME V3 specifies a module's judgement as a MoralTensor
over parties (and further axes) and the library ships EthicalFactsV3 and EthicalJudgementV3.
Nothing ran them: the V2-to-V3 adapter broadcast one vector to every party. Now options given as
EthicalFactsV3 are judged per party, by each module's own rule on the party's view, and the
resulting (9, parties) tensor is collapsed by the tactical layer's party strategy.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import FrozenSet, List

from erisml.ethics.facts import (
    AutonomyAndAgency,
    Consequences,
    EpistemicStatus,
    EthicalFacts,
    JusticeAndFairness,
    Maxim,
    RightsAndDuties,
)
from erisml.ethics.facts_v3 import (
    EthicalFactsV3,
    PartyAutonomy,
    PartyConsequences,
    PartyRights,
)
from erisml.ethics.layers.pipeline import DEMEPipeline, PipelineConfig
from erisml.ethics.modules.base import BaseEthicsModuleV2
from erisml.ethics.modules.tier2.autonomy_consent_em import AutonomyConsentEMV2
from erisml.ethics.moral_vector import MoralVector

PARTIES = ["margaret", "tom"]


def v3(oid, harm=None, consent=None, capacity=None, maxim=None):
    """An option with per-party harm, consent and capacity; the aggregate is the mean harm and
    joint consent, as a V2 builder would record it."""
    harm = harm or {}
    consent = consent or {}
    capacity = capacity or {}
    base = EthicalFacts(
        option_id=oid,
        consequences=Consequences(
            expected_benefit=0.0,
            expected_harm=sum(harm.get(p, 0.0) for p in PARTIES) / len(PARTIES),
            urgency=0.2,
            affected_count=len(PARTIES),
        ),
        rights_and_duties=RightsAndDuties(
            has_valid_consent=all(consent.get(p, True) for p in PARTIES)
        ),
        justice_and_fairness=JusticeAndFairness(),
        autonomy_and_agency=AutonomyAndAgency(),
        epistemic_status=EpistemicStatus(),
    )
    f = EthicalFactsV3.from_v2(base, parties=PARTIES)
    f = replace(
        f,
        consequences=replace(
            f.consequences,
            per_party=tuple(
                PartyConsequences(party_id=p, expected_harm=harm.get(p, 0.0))
                for p in PARTIES
            ),
        ),
        rights_and_duties=replace(
            f.rights_and_duties,
            per_party=tuple(
                PartyRights(party_id=p, consent_given=consent.get(p, True))
                for p in PARTIES
            ),
        ),
        autonomy_and_agency=replace(
            f.autonomy_and_agency,
            per_party=tuple(
                PartyAutonomy(party_id=p, decision_capacity=capacity.get(p))
                for p in PARTIES
            ),
        ),
        maxim=maxim,
    )
    return f


@dataclass
class HarmReader(BaseEthicsModuleV2):
    """Reads the option's harm onto physical_harm; records the parties it saw."""

    em_name: str = "harm_reader"
    em_tier: int = 1
    em_tags: FrozenSet[str] = frozenset()
    seen: List[str] = field(default_factory=list)

    def evaluate_vector(self, facts):
        self.seen.append(f"{facts.option_id}/{facts.metadata.get('party')}")
        return (
            "neutral",
            MoralVector(physical_harm=facts.consequences.expected_harm),
            [],
            {},
        )


def test_a_party_view_carries_that_partys_records_and_the_options_shared_facts():
    maxim = Maxim(action_kind="help", polarity="affirmed")
    f = v3(
        "lift",
        harm={"tom": 0.75},
        consent={"margaret": False},
        capacity={"margaret": "competent"},
        maxim=maxim,
    )
    tom, margaret = f.for_party("tom"), f.for_party("margaret")
    assert (
        tom.consequences.expected_harm == 0.75
        and margaret.consequences.expected_harm == 0.0
    )
    assert (
        margaret.rights_and_duties.has_valid_consent is False
        and tom.rights_and_duties.has_valid_consent
    )
    assert margaret.autonomy_and_agency.decision_capacity == "competent"
    assert (
        tom.maxim == maxim
        and tom.consequences.urgency == 0.2
        and tom.metadata["party"] == "tom"
    )
    assert f.to_v2().maxim == maxim  # the aggregate record keeps the maxim too


def test_each_module_judges_every_party_and_the_tensor_is_9_by_parties():
    em = HarmReader()
    result = DEMEPipeline(ems=[em], config=PipelineConfig()).decide(
        [v3("a", harm={"tom": 0.75})]
    )
    assert sorted(em.seen) == ["a/margaret", "a/tom"]
    assert result.party_verdicts["a"]["harm_reader"] == {
        "margaret": "neutral",
        "tom": "neutral",
    }


def test_harm_concentrated_on_one_party_counts_at_its_worst():
    """Mean harm favours grave harm to one person over moderate harm to two; the worst-case
    collapse does not."""
    concentrated = v3("concentrated", harm={"tom": 0.75})  # mean 0.375
    spread = v3("spread", harm={"margaret": 0.4, "tom": 0.4})  # mean 0.4
    rank1 = DEMEPipeline(ems=[HarmReader()], config=PipelineConfig()).decide(
        [concentrated.to_v2(), spread.to_v2()]
    )
    rank2 = DEMEPipeline(ems=[HarmReader()], config=PipelineConfig()).decide(
        [concentrated, spread]
    )
    assert rank1.selected_option_id == "concentrated"
    assert rank2.selected_option_id == "spread"


def test_a_veto_for_any_party_vetoes_the_option():
    """AutonomyConsent binds a competent person's refusal: Tom refuses, Margaret consents."""
    refused = v3(
        "enter",
        consent={"tom": False},
        capacity={"tom": "competent", "margaret": "competent"},
    )
    other = v3("wait")
    result = DEMEPipeline(ems=[AutonomyConsentEMV2()], config=PipelineConfig()).decide(
        [refused, other]
    )
    assert "enter" in result.forbidden_options and result.selected_option_id == "wait"
    verdicts = result.party_verdicts["enter"][AutonomyConsentEMV2().em_name]
    assert verdicts["tom"] == "veto" and verdicts["margaret"] != "veto"


def test_the_reflex_layer_and_the_deontic_gate_read_the_aggregate_record():
    lie = v3("lie", maxim=Maxim(action_kind="deceive", polarity="affirmed"))
    result = DEMEPipeline(ems=[HarmReader()], config=PipelineConfig()).decide(
        [lie, v3("tell")]
    )
    assert "lie" in result.forbidden_options and result.selected_option_id == "tell"


def test_rank_1_options_are_judged_as_before():
    em = HarmReader()
    result = DEMEPipeline(ems=[em], config=PipelineConfig()).decide([v3("a").to_v2()])
    assert em.seen == ["a/None"] and result.party_verdicts == {}
