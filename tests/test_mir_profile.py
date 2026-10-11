"""An executed governance profile (the lens): it loads only when valid, it runs the pattern it
names, and its hash travels with every result."""

from __future__ import annotations

import json
import math

import pytest

from erisml.ethics.mir import (
    ActionSummary,
    ActorEffect,
    ActorSummary,
    Meta,
    MoralHazardFeatures,
    MoralInterfaceRecord,
)
from erisml.ethics.mir.profile import ProfileError, load_profile

PROFILE = {
    "name": "home_care_robot",
    "version": "1.0",
    "template": "ROUTINE_CIVIL",
    "pattern": "lexicographic",
    "levels": [
        {"name": "safety", "modules": [{"module": "core_physical_safety"}]},
        {
            "name": "rights",
            "modules": [
                {
                    "module": "autonomy_consent",
                    "params": {
                        "allow_override": True,
                        "refusal_only_overridable_when_unanswerable": True,
                    },
                }
            ],
        },
        {
            "name": "oversight",
            "modules": [
                {
                    "module": "human_oversight",
                    "params": {"deferrable_categories": ["autonomous_dispatch"]},
                }
            ],
        },
        {"name": "welfare", "modules": [{"module": "beneficence"}]},
    ],
}


def record():
    actors = (ActorSummary("m", role="civilian", capacity="competent"),)
    actions = (
        ActionSummary(
            "call_ems",
            category="autonomous_dispatch",
            welfare_delta=0.7,
            delta_P_catastrophe=-0.4,
            effects=(ActorEffect("m", True, "refused", injury_risk=0.0),),
        ),
        ActionSummary("check_in", welfare_delta=0.5, effects=(ActorEffect("m"),)),
    )
    hazard = MoralHazardFeatures(
        hazard_immediacy="emerging",
        hazard_severity="serious",
        human_decision_eta=30.0,
        time_to_catastrophe_estimate=900.0,
    )
    return MoralInterfaceRecord(
        Meta("home_care", "US", "2026-10-11T00:00:00Z"), actors, hazard, actions
    )


def test_a_valid_profile_runs_its_pattern_and_carries_its_hash():
    lens = load_profile(PROFILE)
    r = lens.apply(record())
    assert r.selected == "check_in" and r.profile_name == "home_care_robot"
    assert r.profile_hash == lens.hash and len(lens.hash) == 64
    assert r.pattern.mir_hash == record().hash()


def test_the_same_content_gives_the_same_hash_and_any_change_another():
    a, b = load_profile(PROFILE), load_profile(json.loads(json.dumps(PROFILE)))
    assert a.hash == b.hash
    changed = json.loads(json.dumps(PROFILE))
    changed["levels"][1]["modules"][0]["params"]["allow_override"] = False
    assert load_profile(changed).hash != a.hash


def test_a_profile_loads_from_a_json_file(tmp_path):
    p = tmp_path / "lens.json"
    p.write_text(json.dumps(PROFILE), encoding="utf-8")
    assert load_profile(p).hash == load_profile(PROFILE).hash


@pytest.mark.parametrize(
    "mutate,needle",
    [
        (lambda d: d.pop("pattern"), "no 'pattern'"),
        (lambda d: d.update(pattern="free_for_all"), "is not one of"),
        (
            lambda d: d["levels"][0]["modules"].append({"module": "mind_reader"}),
            "unknown module",
        ),
        (
            lambda d: d["levels"][3]["modules"].append(
                {"module": "core_physical_safety"}
            ),
            "appears twice",
        ),
        (lambda d: d["levels"][0]["modules"][0].update(params=[1, 2]), "not a mapping"),
        (lambda d: d["levels"][0]["modules"][0].update(binding="yes"), "not a boolean"),
        (
            lambda d: d["levels"].append({"name": "empty", "modules": []}),
            "has no modules",
        ),
    ],
)
def test_an_invalid_profile_does_not_load(mutate, needle):
    d = json.loads(json.dumps(PROFILE))
    mutate(d)
    with pytest.raises(ProfileError, match=needle):
        load_profile(d)


def test_required_modules_must_be_present():
    with pytest.raises(ProfileError, match="required modules missing"):
        load_profile(PROFILE, required_modules=["autonomy_consent", "privacy"])
    assert (
        load_profile(PROFILE, required_modules=["autonomy_consent"]).name
        == "home_care_robot"
    )


def test_the_lens_changes_the_judgement_and_nothing_else_does():
    """Same MIR, different lens: the refusal binds under one profile and is overridden under the
    other in an imminent mortal hazard with no human reachable (the Accountability Theorem: a
    changed judgement is a changed bond or a changed lens)."""
    actors = (ActorSummary("m", role="civilian", capacity="competent"),)
    actions = (
        ActionSummary(
            "call_ems",
            category="autonomous_dispatch",
            welfare_delta=0.7,
            delta_P_catastrophe=-0.6,
            effects=(ActorEffect("m", True, "refused", injury_risk=0.0),),
        ),
        ActionSummary("check_in", welfare_delta=0.5, effects=(ActorEffect("m"),)),
    )
    hazard = MoralHazardFeatures(
        hazard_immediacy="imminent",
        hazard_severity="mortal",
        human_decision_eta=math.inf,
        time_to_catastrophe_estimate=60.0,
    )
    m = MoralInterfaceRecord(
        Meta("home_care", "US", "2026-10-11T00:00:00Z"), actors, hazard, actions
    )
    binding = load_profile(PROFILE)
    guide_default = json.loads(json.dumps(PROFILE))
    guide_default["levels"][1]["modules"][0]["params"][
        "refusal_only_overridable_when_unanswerable"
    ] = False
    assert binding.apply(m).selected == "check_in"
    assert load_profile(guide_default).apply(m).selected == "call_ems"


def test_a_lens_result_becomes_a_chained_decision_proof():
    lens = load_profile(PROFILE)
    first = lens.apply(record()).proof()
    second = lens.apply(record()).proof(previous=first)
    assert first.input_facts_hash == record().hash() and first.profile_hash == lens.hash
    assert (
        first.selected_option_id == "check_in" and "call_ems" in first.forbidden_options
    )
    assert [lo.layer_name for lo in first.layer_outputs] == [
        "safety",
        "rights",
        "oversight",
        "welfare",
    ]
    assert first.verify_hash() and second.verify_chain(first) and second.verify_hash()
