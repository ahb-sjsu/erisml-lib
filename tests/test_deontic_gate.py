"""Tests for the deontic maxim gate (Kantian universalizability with polarity)."""

from __future__ import annotations

from erisml.ethics.deme import DEME
from erisml.ethics.deontic_gate import evaluate_maxim
from erisml.ethics.facts import (
    Consequences,
    EthicalFacts,
    JusticeAndFairness,
    Maxim,
    RightsAndDuties,
)
from erisml.ethics.layers.pipeline import DEMEPipeline

# ----------------------------------------------------- gate logic


def test_affirmed_prohibition_vetoes():
    r = evaluate_maxim(Maxim(action_kind="deceive"))
    assert r.vetoed is True
    assert r.passes is False


def test_negated_prohibition_passes():
    r = evaluate_maxim(Maxim(action_kind="deceive", polarity="negated"))
    assert r.vetoed is False
    assert r.action_kind == "not:deceive"


def test_affirmed_imperfect_duty_passes():
    assert evaluate_maxim(Maxim(action_kind="help")).vetoed is False


def test_negated_imperfect_duty_vetoes():
    r = evaluate_maxim(Maxim(action_kind="help", polarity="negated"))
    assert r.vetoed is True
    assert r.contradiction_type == "contradiction_in_will"


def test_negated_permissible_act_passes():
    # Not making a promise is permissible — no veto.
    r = evaluate_maxim(Maxim(action_kind="make_or_keep_commitment", polarity="negated"))
    assert r.vetoed is False


def test_unknown_and_missing_never_veto():
    assert evaluate_maxim(Maxim(action_kind="mystery")).vetoed is False
    assert evaluate_maxim(None).vetoed is False
    assert evaluate_maxim(Maxim(action_kind=None)).vetoed is False


# ----------------------------------------------------- DEME public API


def test_deme_evaluate_forbids_failing_maxim():
    j = DEME().evaluate(Maxim(action_kind="deceive"))
    assert j.verdict == "FORBID"
    assert "deontic_gate" in j.metadata


def test_deme_evaluate_allows_ok_maxim():
    assert DEME().evaluate(Maxim(action_kind="protect")).verdict == "ALLOW"


# ----------------------------------------------------- pipeline integration


def test_pipeline_vetoes_option_with_failing_maxim():
    # complete facts: the default reflex rules read the rights and justice blocks, and an
    # option missing them is vetoed fail-closed (tests/test_pipeline_selection_safety.py)
    blocks = dict(
        consequences=Consequences(),
        rights_and_duties=RightsAndDuties(),
        justice_and_fairness=JusticeAndFairness(),
    )
    good = EthicalFacts(option_id="good", **blocks)
    bad = EthicalFacts(option_id="bad", maxim=Maxim(action_kind="deceive"), **blocks)
    result = DEMEPipeline().decide([good, bad])
    assert "bad" in result.forbidden_options
    assert "good" not in result.forbidden_options
