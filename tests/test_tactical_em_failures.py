"""An ethics module that raises has not approved anything: the tactical layer records it.

Before, TacticalLayer.evaluate caught every exception from an EM and dropped it, so a module
that crashed (or a V1 module added to a V2 pipeline without its adapter) looked exactly like a
module that raised no objection.
"""

from __future__ import annotations

from erisml.ethics.facts import (
    Consequences,
    EthicalFacts,
    JusticeAndFairness,
    RightsAndDuties,
)
from erisml.ethics.layers.pipeline import DEMEPipeline, PipelineConfig
from erisml.ethics.layers.tactical import TacticalLayer, TacticalLayerConfig
from erisml.ethics.modules.base import V1ToV2Adapter
from erisml.ethics.modules.greek_tragedy_tragic_conflict_em import TragicConflictEM
from erisml.ethics.modules.tier0.geneva_em import GenevaEMV2


class Broken:
    em_name = "broken"
    em_tier = 1
    stakeholder = "test"

    def judge(self, facts):
        raise RuntimeError("model file missing")


def option(option_id="a", harm=0.0, urgency=0.0):
    return EthicalFacts(
        option_id=option_id,
        consequences=Consequences(
            expected_benefit=0.5, expected_harm=harm, urgency=urgency
        ),
        rights_and_duties=RightsAndDuties(),
        justice_and_fairness=JusticeAndFairness(),
    )


def test_a_failing_em_is_recorded_and_the_others_still_judge():
    r = TacticalLayer([GenevaEMV2(), Broken()]).evaluate(option())
    assert r.em_failures == ["broken: RuntimeError: model file missing"]
    assert [j.em_name for j in r.judgements] == ["geneva_constitutional"]
    assert not r.vetoed  # the default keeps the earlier behaviour


def test_fail_closed_turns_a_failure_into_a_veto():
    r = TacticalLayer(
        [GenevaEMV2(), Broken()], TacticalLayerConfig(fail_closed=True)
    ).evaluate(option())
    assert r.vetoed and r.veto_reasons == ["broken: failed (RuntimeError); fail_closed"]


def test_a_v1_em_added_without_its_adapter_is_a_recorded_failure_not_a_silent_one():
    r = TacticalLayer([TragicConflictEM()]).evaluate(option())
    assert len(r.em_failures) == 1 and r.em_failures[0].startswith(
        "tragic_conflict: AttributeError"
    )
    assert r.judgements == []


def test_through_the_adapter_tragic_conflict_judges_and_keeps_its_index():
    em = V1ToV2Adapter(TragicConflictEM(), em_tier=3)
    r = TacticalLayer([em]).evaluate(option(harm=0.85, urgency=0.9))
    assert r.em_failures == []
    meta = r.judgements[0].metadata
    assert (
        meta["tragic_conflict_high"] is True and meta["tragic_conflict_index"] >= 0.55
    )
    assert (
        "severe_harm" in meta["triggers"] and not r.vetoed
    )  # it flags, it never vetoes


def test_the_pipeline_reports_failures_per_option_and_in_the_proof():
    result = DEMEPipeline(ems=[GenevaEMV2(), Broken()], config=PipelineConfig()).decide(
        [option("a"), option("b")]
    )
    assert set(result.em_failures) == {"a", "b"}
    tactical = next(
        layer for layer in result.proof.layer_outputs if layer.layer_name == "tactical"
    )
    assert tactical.output_data["em_failures"] == result.em_failures


def test_no_failures_means_an_empty_record():
    result = DEMEPipeline(ems=[GenevaEMV2()]).decide([option("a")])
    assert result.em_failures == {}
