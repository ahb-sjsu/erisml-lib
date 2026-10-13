"""DEMEPipeline never selects what it forbids, advisory tiers do not exclude, the default
pipeline runs its reflex rules, and decision proofs chain.

Each test fails on the pipeline before this fix:
- a module that forbids without setting a vector veto flag left its option ranked and selected,
  because ranking filtered on vector flags rather than on the forbidden set;
- an advisory (tier 3) module's veto flag removed an option from the ranking although that tier
  may not veto, so the option was neither ranked nor listed as forbidden;
- PipelineConfig passed an explicit empty ReflexLayerConfig, so DEMEPipeline() held zero reflex
  rules;
- previous_proof_hash was never set, so proofs were hashed but not chained.
"""

from __future__ import annotations

from dataclasses import dataclass

from erisml.ethics.facts import (
    Consequences,
    EthicalFacts,
    JusticeAndFairness,
    RightsAndDuties,
)
from erisml.ethics.layers.pipeline import DEMEPipeline
from erisml.ethics.modules.base import BaseEthicsModuleV2
from erisml.ethics.moral_vector import MoralVector


def option(option_id, benefit=0.5, harm=0.0, violates_rights=False):
    return EthicalFacts(
        option_id=option_id,
        consequences=Consequences(expected_benefit=benefit, expected_harm=harm),
        rights_and_duties=RightsAndDuties(violates_rights=violates_rights),
        justice_and_fairness=JusticeAndFairness(),
    )


@dataclass
class ForbidsWithoutFlag(BaseEthicsModuleV2):
    """Forbids option 'bad' by verdict alone, scoring it best, with no vector veto flag."""

    em_name: str = "forbids_without_flag"
    em_tier: int = 1

    def evaluate_vector(self, facts):
        if facts.option_id == "bad":
            return (
                "forbid",
                MoralVector(physical_harm=0.0),
                ["forbidden by verdict"],
                {},
            )
        return "neutral", MoralVector(physical_harm=0.5), [], {}


@dataclass
class AdvisoryFlagger(BaseEthicsModuleV2):
    """A tier-3 (advisory) module that sets a veto flag on option 'flagged'."""

    em_name: str = "advisory_flagger"
    em_tier: int = 3

    def evaluate_vector(self, facts):
        flags = ["ADVISORY_CONCERN"] if facts.option_id == "flagged" else []
        return "neutral", MoralVector(veto_flags=flags), [], {}


def test_an_option_forbidden_by_verdict_is_never_selected():
    result = DEMEPipeline(ems=[ForbidsWithoutFlag()]).decide(
        [option("bad"), option("ok")]
    )
    assert "bad" in result.forbidden_options
    assert "bad" not in result.ranked_options
    assert result.selected_option_id == "ok"


def test_a_lone_forbidden_option_leaves_nothing_selected():
    result = DEMEPipeline(ems=[ForbidsWithoutFlag()]).decide([option("bad")])
    assert result.selected_option_id is None and result.ranked_options == []


def test_an_advisory_tier_flag_does_not_exclude_an_option():
    result = DEMEPipeline(ems=[AdvisoryFlagger()]).decide(
        [option("flagged"), option("plain")]
    )
    assert "flagged" not in result.forbidden_options
    assert "flagged" in result.ranked_options


def test_the_default_pipeline_runs_its_reflex_rules():
    pipeline = DEMEPipeline()
    assert len(pipeline.reflex.config.veto_rules) == 3
    result = pipeline.decide([option("rights", violates_rights=True), option("fine")])
    assert result.forbidden_options == ["rights"]
    assert result.selected_option_id == "fine"


def test_decision_proofs_chain():
    pipeline = DEMEPipeline(ems=[ForbidsWithoutFlag()])
    first = pipeline.decide([option("ok")]).proof
    second = pipeline.decide([option("ok")]).proof
    assert first.previous_proof_hash is None and first.verify_chain(None)
    assert second.previous_proof_hash == first.proof_hash
    assert second.verify_chain(first) and second.verify_hash()


def test_an_option_missing_the_blocks_the_reflex_reads_is_vetoed_fail_closed():
    """A default reflex rule that cannot read its block vetoes (ReflexLayerConfig.fail_open is
    False): an option the pipeline cannot check is not passed as if it had been checked.
    """
    result = DEMEPipeline().decide([EthicalFacts(option_id="bare"), option("fine")])
    assert result.forbidden_options == ["bare"] and result.selected_option_id == "fine"
