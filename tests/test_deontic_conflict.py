"""A prohibited act whose purpose is an imperfect duty is a tragic conflict, escalated, not vetoed.

Before, the gate vetoed every affirmed prohibition, so "deceive to protect those in my care"
(the Nazi-attic lie) was simply forbidden. The owner decided (12 October 2026) that such a
maxim is a conflict between the perfect duty not to deceive and the imperfect duty to protect,
which DEME escalates to a human.
"""

from erisml.ethics.deontic_gate import evaluate_maxim
from erisml.ethics.facts import (
    Consequences,
    EthicalFacts,
    JusticeAndFairness,
    Maxim,
    RightsAndDuties,
)
from erisml.ethics.layers.pipeline import DEMEPipeline


def option(oid, maxim):
    return EthicalFacts(
        option_id=oid,
        consequences=Consequences(),
        rights_and_duties=RightsAndDuties(),
        justice_and_fairness=JusticeAndFairness(),
        maxim=maxim,
    )


def test_deceiving_to_protect_is_a_conflict_not_a_veto():
    r = evaluate_maxim(Maxim(action_kind="deceive", purpose_kind="protect"))
    assert r.conflict and not r.vetoed and not r.passes
    assert "tragic conflict" in r.reason


def test_deceiving_for_any_other_purpose_is_still_vetoed():
    for purpose in (None, "deceive", "make_or_keep_commitment"):
        r = evaluate_maxim(Maxim(action_kind="deceive", purpose_kind=purpose))
        assert r.vetoed and not r.conflict, purpose


def test_omitting_an_imperfect_duty_is_unchanged():
    r = evaluate_maxim(
        Maxim(action_kind="help", polarity="negated", purpose_kind="protect")
    )
    assert r.vetoed and not r.conflict


def test_the_pipeline_escalates_a_conflict_and_still_forbids_a_plain_prohibition():
    result = DEMEPipeline().decide(
        [
            option(
                "lie_to_protect", Maxim(action_kind="deceive", purpose_kind="protect")
            ),
            option("lie_for_gain", Maxim(action_kind="deceive")),
        ]
    )
    assert "lie_to_protect" not in result.forbidden_options
    assert "lie_to_protect" in result.escalations
    assert result.forbidden_options == ["lie_for_gain"]
    reflex = next(o for o in result.proof.layer_outputs if o.layer_name == "reflex")
    assert "lie_to_protect" in reflex.output_data["deontic_conflicts"]
