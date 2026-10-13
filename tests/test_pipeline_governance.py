"""DEMEPipeline executes a governance profile.

Each test fails on the pipeline before this change, which ignored governance entirely: it
ranked by fixed default dimension weights, weighed EMs by fixed tier weights, let no explicit
veto EM veto outside its tier, ran disabled tiers, always preferred a baseline within 5% of the
best, had no score threshold, averaged stakeholders together, and built a profile's pipeline
with no reflex rules, every registered EM, and no profile name or hash in its proofs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import pytest

from erisml.ethics.facts import (
    Consequences,
    EthicalFacts,
    JusticeAndFairness,
    RightsAndDuties,
)
from erisml.ethics.governance.config_v2 import (
    AggregationStrategy,
    DimensionWeights,
    GovernanceConfigV2,
    TierConfig,
)
from erisml.ethics.interop.profile_adapters import pipeline_from_profile, profile_hash
from erisml.ethics.layers.pipeline import DEMEPipeline, PipelineConfig
from erisml.ethics.modules.base import BaseEthicsModuleV2
from erisml.ethics.moral_vector import MoralVector
from erisml.ethics.profile_v04 import DEMEProfileV04


def option(option_id, violates_rights=False):
    return EthicalFacts(
        option_id=option_id,
        consequences=Consequences(expected_benefit=0.5, expected_harm=0.0),
        rights_and_duties=RightsAndDuties(violates_rights=violates_rights),
        justice_and_fairness=JusticeAndFairness(),
    )


@dataclass
class Scripted(BaseEthicsModuleV2):
    """Returns a given vector (and verdict) per option."""

    em_name: str = "scripted"
    em_tier: int = 2
    stakeholder: str = "everyone"
    vectors: Dict[str, MoralVector] = field(default_factory=dict)
    forbid: tuple = ()

    def evaluate_vector(self, facts):
        verdict = "forbid" if facts.option_id in self.forbid else "neutral"
        return verdict, self.vectors.get(facts.option_id, MoralVector()), [], {}


def governed(ems, **gov):
    return DEMEPipeline(
        ems=ems, config=PipelineConfig(governance=GovernanceConfigV2(**gov))
    )


SAFE_BUT_CONTROLLING = MoralVector(physical_harm=0.0, autonomy_respect=0.0)
FREE_BUT_RISKY = MoralVector(physical_harm=0.6, autonomy_respect=1.0)


def test_the_profile_s_dimension_weights_decide_the_ranking():
    em = Scripted(vectors={"safe": SAFE_BUT_CONTROLLING, "free": FREE_BUT_RISKY})
    opts = [option("safe"), option("free")]
    harm_first = DimensionWeights(physical_harm=10.0, autonomy_respect=0.1)
    autonomy_first = DimensionWeights(physical_harm=0.1, autonomy_respect=10.0)
    assert (
        governed([em], dimension_weights=harm_first).decide(opts).selected_option_id
        == "safe"
    )
    assert (
        governed([em], dimension_weights=autonomy_first).decide(opts).selected_option_id
        == "free"
    )


def test_an_explicit_veto_em_vetoes_outside_a_veto_tier():
    advisory = Scripted(em_name="advisory", em_tier=3, forbid=("x",))
    opts = [option("x"), option("y")]
    assert "x" not in DEMEPipeline(ems=[advisory]).decide(opts).forbidden_options
    result = governed([advisory], veto_ems=["advisory"]).decide(opts)
    assert "x" in result.forbidden_options and result.selected_option_id == "y"


def test_a_disabled_tier_does_not_run_but_tier_0_always_does():
    tiers = {0: TierConfig(enabled=False), 3: TierConfig(enabled=False)}
    soft = Scripted(em_name="soft", em_tier=3)
    constitutional = Scripted(em_name="constitutional", em_tier=0, forbid=("x",))
    result = governed([soft, constitutional], tier_configs=tiers).decide(
        [option("x"), option("y")]
    )
    ran = {j.em_name for j in result.proof.em_judgements}
    assert ran == {"constitutional"} and "x" in result.forbidden_options


def test_the_baseline_is_preferred_only_under_the_status_quo_tie_breaker():
    em = Scripted(
        vectors={"act": MoralVector(), "stay": MoralVector(autonomy_respect=0.9)}
    )
    opts = [option("act"), option("stay")]
    assert DEMEPipeline(ems=[em]).decide(opts, "stay").selected_option_id == "stay"
    assert governed([em]).decide(opts, "stay").selected_option_id == "act"
    assert (
        governed([em], tie_breaker="status_quo").decide(opts, "stay").selected_option_id
        == "stay"
    )


def test_the_score_threshold_excludes_low_options():
    em = Scripted(vectors={"poor": MoralVector(physical_harm=1.0, rights_respect=0.0)})
    result = governed([em], min_score_threshold=0.9).decide(
        [option("poor"), option("ok")]
    )
    assert result.ranked_options == ["ok"] and result.selected_option_id == "ok"


def test_worst_off_aggregation_prefers_the_option_no_party_bears():
    def party(name, fair, skewed):
        return Scripted(
            em_name=name,
            stakeholder=name,
            vectors={
                "fair": MoralVector(autonomy_respect=fair),
                "skewed": MoralVector(autonomy_respect=skewed),
            },
        )

    ems = [party("p1", 0.6, 1.0), party("p2", 0.6, 0.3)]
    opts = [option("fair"), option("skewed")]
    others = [d for d in MoralVector.core_dimension_names() if d != "autonomy_respect"]
    only_autonomy = DimensionWeights(**{d: 0.0 for d in others})
    mean = governed(ems, dimension_weights=only_autonomy).decide(opts)
    worst = governed(
        ems,
        dimension_weights=only_autonomy,
        stakeholder_aggregation=AggregationStrategy.MIN,
    ).decide(opts)
    assert mean.selected_option_id == "skewed"  # 0.65 on average
    assert worst.selected_option_id == "fair"  # 0.6 for the worst-off party, not 0.3


def test_a_profile_pipeline_runs_its_base_em_reflex_rules_and_records_the_profile():
    profile = DEMEProfileV04(name="home", description="d", stakeholder_label="resident")
    pipe = pipeline_from_profile(profile)
    assert [em.em_name for em in pipe.tactical.ems][0] == "geneva_constitutional"
    result = pipe.decide([option("harmful", violates_rights=True), option("ok")])
    assert "harmful" in result.forbidden_options
    assert result.proof.profile_name == "home"
    assert result.proof.profile_hash == profile_hash(profile) != ""


def test_a_profile_naming_an_unregistered_em_is_refused():
    profile = DEMEProfileV04(
        name="p", description="d", stakeholder_label="s", active_em_names=["no_such_em"]
    )
    with pytest.raises(ValueError, match="no_such_em"):
        pipeline_from_profile(profile)


def test_a_profile_naming_its_ems_runs_exactly_those():
    profile = DEMEProfileV04(
        name="p",
        description="d",
        stakeholder_label="s",
        active_em_names=["autonomy_consent"],
    )
    names = [em.em_name for em in pipeline_from_profile(profile).tactical.ems]
    assert names == ["geneva_constitutional", "autonomy_consent"]
