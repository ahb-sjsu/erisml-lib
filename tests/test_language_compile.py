"""The ErisML language end to end: every block reaches the AST, expressions keep their
operators, and a parsed model compiles to objects that run.

Before November 2026 a norms block crashed the parser, a binary expression lost its operator
and right-hand side, and the ethics and dynamics blocks were parsed and thrown away.
"""

import pytest

from erisml.core.engine import ErisEngine
from erisml.core.norms import NormViolation
from erisml.core.types import ActionInstance, EnvironmentRule
from erisml.ethics.interop.profile_adapters import pipeline_from_profile
from erisml.language import (
    CompileError,
    ParsingError,
    build_model,
    ethics_profile,
    evaluate,
    norm_texts,
    parse_erisml,
)

SOURCE = """
// a small home
environment TinyHome {
  objects: Room, Person;
  state:
    location_robot: str;
    light_on: Room -> bool;
    battery: real;
    occupied: bool;
}
agent Robot {
  capabilities: move_robot toggle_light;
  beliefs: map;
}
norms Safety {
  prohibition: action.agent == Robot && action.name == move_robot && action.to == "r2";
  obligation: !occupied || battery >= 0.2;
  sanction: battery < 0.1 && (action.name == move_robot || action.name == toggle_light);
}
ethics Care {
  moral_vector { physical_harm: 2.0; autonomy_respect: 1.5; epistemic_quality: 0.25; }
  tier 0 { enabled: true; weight: 10; veto_enabled: true; }
  tier 3 { weight: 0.5; veto_enabled: false; }
  em core_physical_safety { tier: 1; weight: 2; veto_capable: true; tags: "safety", "harm"; }
  em beneficence { tier: 3; }
  veto when battery < 0.05 { flag: "LOW_BATTERY"; reason: "cannot act safely"; }
}
dynamics {
  joint_action { Robot.move_robot -> cost 1.5; Robot.toggle_light -> cost 0.1; }
  reward { tidy: occupied && battery > 0.5; }
}
"""

STATE = {
    "location_robot": "r1",
    "light_on": {"r1": False},
    "battery": 0.9,
    "occupied": True,
}


def move(state, params):
    new = dict(state)
    new["location_robot"] = params["to"]
    return new


RULES = {"move_robot": EnvironmentRule("move_robot", ["from", "to"], move)}


def to(room):
    return ActionInstance("Robot", "move_robot", {"from": "r1", "to": room})


# ---------------------------------------------------------------- parsing


def test_every_block_reaches_the_ast():
    ast = parse_erisml(SOURCE)
    assert ast.environment.object_types == ["Room", "Person"]
    light = ast.environment.state_vars[1].type
    assert (light.kind, light.base, light.key_object_type) == (
        "mapping",
        "bool",
        "Room",
    )
    assert ast.agents[0].capabilities == ["move_robot", "toggle_light"]
    assert [r.kind for r in ast.norms.rules] == [
        "prohibition",
        "obligation",
        "sanction",
    ]
    assert ast.ethics.name == "Care" and len(ast.ethics.ems) == 2
    assert ast.dynamics.joint_actions[0].cost == 1.5
    assert ast.dynamics.rewards[0].name == "tidy"


def test_an_expression_keeps_its_operators_and_its_structure():
    rules = parse_erisml(SOURCE).norms.rules
    assert norm_texts(parse_erisml(SOURCE))[0] == (
        "prohibition: (((action.agent == Robot) && (action.name == move_robot)) "
        '&& (action.to == "r2"))'
    )
    assert rules[1].expr == "(!occupied || (battery >= 0.2))"
    assert rules[0].tree.names() == [
        "action.agent",
        "Robot",
        "action.name",
        "move_robot",
        "action.to",
    ]


def test_precedence_is_or_then_and_then_not_then_comparison():
    src = SOURCE.replace(
        "obligation: !occupied || battery >= 0.2;", "obligation: a || b && !c == d;"
    )
    assert parse_erisml(src).norms.rules[1].expr == "(a || (b && !(c == d)))"


def test_the_ethics_block_is_read_in_full():
    e = parse_erisml(SOURCE).ethics
    assert e.moral_vector.weights == {
        "physical_harm": 2.0,
        "autonomy_respect": 1.5,
        "epistemic_quality": 0.25,
    }
    tiers = {t.tier: t for t in e.tier_configs}
    assert tiers[0].weight == 10.0 and tiers[3].veto_enabled is False
    safety = e.ems[0]
    assert (safety.name, safety.tier, safety.veto_capable) == (
        "core_physical_safety",
        1,
        True,
    )
    assert safety.tags == ["safety", "harm"]
    veto = e.veto_rules[0]
    assert (veto.condition_expr, veto.flag) == ("(battery < 0.05)", "LOW_BATTERY")
    assert veto.reason == "cannot act safely"


def test_the_language_does_not_fix_the_read_out_names():
    """Which read-outs exist is the consumer's business: the nine hand-made dimensions are
    being replaced by discovered coordinates with named read-outs."""
    src = SOURCE.replace(
        "physical_harm: 2.0;", "identity_attack: 0.6; physical_harm: 2.0;"
    )
    weights = parse_erisml(src).ethics.moral_vector.weights
    assert weights["identity_attack"] == 0.6
    with pytest.raises(CompileError, match="identity_attack"):
        ethics_profile(parse_erisml(src).ethics)


@pytest.mark.parametrize(
    "old, new, message",
    [
        ("battery >= 0.2;", "battery >= ;", "line 17"),
        ("physical_harm: 2.0;", "physical_harm: 2.0; physical_harm: 1;", "twice"),
        (
            "tier 3 {",
            "tier 0 { enabled: false; } tier 3 {",
            "tier 0 is configured twice",
        ),
        ("em beneficence { tier: 3; }", "em beneficence { tier: 7; }", "line"),
    ],
)
def test_a_bad_source_is_a_parsing_error_that_says_where(old, new, message):
    assert old in SOURCE
    with pytest.raises(ParsingError, match=message):
        parse_erisml(SOURCE.replace(old, new))


def test_a_minimal_model_needs_only_an_environment_and_an_agent():
    ast = parse_erisml(
        "environment E { objects: T; state: } agent A { capabilities: ; }"
    )
    assert ast.norms is None and ast.ethics is None and ast.dynamics is None
    assert build_model(ast).norms is None


# ---------------------------------------------------------------- compiling


def test_a_parsed_model_runs_and_its_norms_gate_actions():
    model = build_model(
        parse_erisml(SOURCE), instances={"Room": ["r1", "r2"]}, rules=RULES
    )
    assert model.env.object_types["Room"].instances == ["r1", "r2"]
    assert model.env.state_vars["light_on"].domain.is_mapping
    assert model.agents["Robot"].capabilities["move_robot"].param_names == [
        "from",
        "to",
    ]
    assert model.agents["Robot"].capabilities["toggle_light"].param_names == []

    assert [r.name for r in model.norms.check_prohibitions(STATE, to("r2"))] == [
        "prohibition_1"
    ]
    assert model.norms.check_prohibitions(STATE, to("r1")) == []
    low = dict(STATE, battery=0.05)
    assert [r.name for r in model.norms.sanctions_triggered(low, to("r1"))] == [
        "sanction_1"
    ]
    assert model.norms.sanctions_triggered(STATE, to("r1")) == []

    engine = ErisEngine(model)
    with pytest.raises(NormViolation):
        engine.step(dict(STATE), to("r2"))
    assert engine.step(dict(STATE), to("r1"))["location_robot"] == "r1"


def test_evaluation_reads_state_action_fields_and_symbols():
    rule = parse_erisml(SOURCE).norms.rules[0].tree
    assert evaluate(rule, STATE, to("r2")) is True
    assert (
        evaluate(rule, STATE, ActionInstance("Human", "move_robot", {"to": "r2"}))
        is False
    )
    obligation = parse_erisml(SOURCE).norms.rules[1].tree
    assert evaluate(obligation, dict(STATE, battery=0.1), None) is False
    assert evaluate(obligation, dict(STATE, occupied=False, battery=0.1), None) is True
    # an action without the parameter a comparison reads is not less than anything
    src = SOURCE.replace('action.to == "r2";', "action.speed > 3;")
    fast = parse_erisml(src).norms.rules[0].tree
    assert evaluate(fast, STATE, to("r1")) is False


@pytest.mark.parametrize(
    "kwargs, source, message",
    [
        ({"instances": {"Shelf": ["s1"]}}, SOURCE, "undeclared object types"),
        (
            {"rules": {"fly": EnvironmentRule("fly", [], move)}},
            SOURCE,
            "no agent can take",
        ),
        (
            {},
            SOURCE.replace("light_on: Room -> bool;", "light_on: Shelf -> bool;"),
            "undeclared object type Shelf",
        ),
        (
            {},
            SOURCE.replace("action.agent == Robot", "Robot.battery == 1"),
            "only action.<field>",
        ),
    ],
)
def test_a_model_that_cannot_be_built_says_why(kwargs, source, message):
    with pytest.raises(CompileError, match=message):
        build_model(parse_erisml(source), **kwargs)


def test_the_ethics_block_becomes_a_profile_the_pipeline_executes():
    profile = ethics_profile(parse_erisml(SOURCE).ethics, composition="hard_shell")
    w = profile.moral_dimension_weights
    assert (w.physical_harm, w.autonomy_respect, w.epistemic_quality) == (
        2.0,
        1.5,
        0.25,
    )
    assert w.privacy_protection == 1.0  # not mentioned: the default stands
    assert profile.tier_configs[3].weight_multiplier == 0.5
    assert profile.tier_configs[3].veto_enabled is False
    assert profile.active_em_names == ["core_physical_safety", "beneficence"]
    assert profile.composition == "hard_shell"
    names = [em.em_name for em in pipeline_from_profile(profile).tactical.ems]
    assert names == ["geneva_constitutional", "core_physical_safety", "beneficence"]
