"""The MoralInterfaceRecord v1.0, the lexicographic pattern and the MIR modules, each tested
against its clause of docs/guides/DEME_EFM_Design_Guide_v0.1.md."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pytest

from erisml.ethics.mir import (
    ActionSummary,
    ActionVerdict,
    ActorEffect,
    ActorSummary,
    Level,
    Meta,
    MIRError,
    MIRJudgement,
    ModuleSlot,
    MoralHazardFeatures,
    MoralInterfaceRecord,
    predicates,
    run_lexicographic,
)
from erisml.ethics.mir.modules import (
    AutonomyConsentEM,
    BeneficenceEM,
    CorePhysicalSafetyEM,
    HumanOversightEM,
    PrivacyEM,
    ProxemicsSafetyEM,
)

META = Meta(
    domain_id="home_care", jurisdiction_id="US", timestamp="2026-10-11T00:00:00Z"
)


def mir(actions, actors=None, **hazard):
    actors = actors or [
        ActorSummary(
            "m", role="civilian", vulnerability_flags=("elderly",), capacity="competent"
        )
    ]
    return MoralInterfaceRecord(
        META, tuple(actors), MoralHazardFeatures(**hazard), tuple(actions)
    )


def act(action_id, consent=None, affects=False, **kw):
    effects = (
        ActorEffect(
            "m",
            substantially_affects=affects,
            consent=consent or "unknown",
            injury_risk=kw.pop("injury", None),
        ),
    )
    return ActionSummary(action_id, effects=effects, **kw)


# ---------------------------------------------------------------- the record (Guide 2)


def test_unknown_is_a_value_not_a_permission():
    e = ActorEffect("m")
    assert e.consent == "unknown" and e.substantially_affects is False
    assert ActorSummary("m").capacity == "unknown"
    assert MoralHazardFeatures().hazard_immediacy is None


@pytest.mark.parametrize(
    "bad",
    [
        lambda: ActorSummary("m", role="neighbour"),
        lambda: ActorSummary("m", capacity="fine"),
        lambda: ActorEffect("m", consent="maybe"),
        lambda: MoralHazardFeatures(hazard_immediacy="soon"),
        lambda: MoralHazardFeatures(P_catastrophe_if_no_action=1.5),
        lambda: ActionSummary("a", delta_P_catastrophe=-2.0),
        lambda: mir([ActionSummary("a", effects=(ActorEffect("ghost"),))]),
        lambda: mir([ActionSummary("a"), ActionSummary("a")]),
    ],
)
def test_the_schema_rejects_what_v1_does_not_define(bad):
    with pytest.raises(MIRError):
        bad()


def test_the_hash_is_canonical_and_handles_an_unreachable_human():
    a = mir([ActionSummary("x")], human_decision_eta=math.inf)
    b = mir([ActionSummary("x")], human_decision_eta=math.inf)
    assert a.hash() == b.hash() and len(a.hash()) == 64
    assert a.hash() != mir([ActionSummary("y")], human_decision_eta=math.inf).hash()


def test_a_predicate_with_unknown_inputs_is_unknown_not_false():
    p = predicates(mir([ActionSummary("x")]), theta_prob=0.5, theta_count=10)
    assert p["presents_immediate_large_scale_mortal_danger_to_innocents"] is None
    full = mir(
        [ActionSummary("x")],
        hazard_immediacy="imminent",
        hazard_severity="mortal",
        hazard_scope="crowd",
        targets_profile="mostly_innocents",
        P_catastrophe_if_no_action=0.8,
        num_persons_at_risk=40,
    )
    assert (
        predicates(full, 0.5, 10)[
            "presents_immediate_large_scale_mortal_danger_to_innocents"
        ]
        is True
    )


# ---------------------------------------------------------------- the lexicographic stack (Guide 5.3)


@dataclass(frozen=True)
class Fixed:
    name: str
    verdicts: dict
    binding: bool = True
    tier: int = 2
    raises: bool = False

    def evaluate(self, m, params):
        if self.raises:
            raise RuntimeError("broken")
        return MIRJudgement(self.name, {k: v for k, v in self.verdicts.items()})


def test_no_lower_level_reintroduces_an_action():
    m = mir([ActionSummary("a"), ActionSummary("b")])
    upper = Level(
        "upper",
        (
            ModuleSlot(
                Fixed("veto_a", {"a": ActionVerdict(veto=True), "b": ActionVerdict()})
            ),
        ),
    )
    lower = Level(
        "lower",
        (
            ModuleSlot(
                Fixed(
                    "loves_a",
                    {"a": ActionVerdict(score=1.0), "b": ActionVerdict(score=0.0)},
                    binding=False,
                )
            ),
        ),
    )
    r = run_lexicographic(m, [upper, lower])
    assert r.ranked == ["b"] and "a" in r.vetoed


def test_a_failing_module_vetoes_its_level_and_marks_health():
    m = mir([ActionSummary("a")])
    r = run_lexicographic(
        m, [Level("l", (ModuleSlot(Fixed("broken", {}, raises=True)),))]
    )
    assert (
        r.ranked == []
        and r.health_ok is False
        and r.vetoed["a"] == ["broken: failed (RuntimeError)"]
    )


def test_a_binding_module_silent_about_an_action_has_not_cleared_it():
    m = mir([ActionSummary("a"), ActionSummary("b")])
    r = run_lexicographic(
        m, [Level("l", (ModuleSlot(Fixed("half", {"a": ActionVerdict()})),))]
    )
    assert r.ranked == ["a"] and r.vetoed["b"] == ["half: no verdict"]


def test_an_advisory_module_cannot_veto_and_a_soft_block_is_kept():
    m = mir([ActionSummary("a"), ActionSummary("b")])
    adv = Fixed(
        "adv", {"a": ActionVerdict(veto=True), "b": ActionVerdict()}, binding=False
    )
    soft = Fixed(
        "law",
        {
            "a": ActionVerdict(
                soft_block=True, annotations={"reason": "needs authorization"}
            ),
            "b": ActionVerdict(),
        },
    )
    r = run_lexicographic(m, [Level("l", (ModuleSlot(adv), ModuleSlot(soft)))])
    assert r.ranked == ["a", "b"] and r.soft_blocked == {
        "a": ["law: needs authorization"]
    }


def test_a_scoring_level_keeps_the_best_subset_and_ties_keep_list_order():
    m = mir([ActionSummary("a"), ActionSummary("b"), ActionSummary("c")])
    s = Fixed(
        "s",
        {
            "a": ActionVerdict(score=0.5),
            "b": ActionVerdict(score=0.9),
            "c": ActionVerdict(score=0.9),
        },
        binding=False,
    )
    r = run_lexicographic(m, [Level("utility", (ModuleSlot(s),))])
    assert r.ranked == ["b", "c"]


# ---------------------------------------------------------------- AutonomyConsent (Guide 4.3.1)


def consent_verdict(m, **params):
    return AutonomyConsentEM().evaluate(m, params).per_action


def test_a_competent_refusal_or_absent_consent_vetoes_an_act_that_affects_her():
    v = consent_verdict(
        mir(
            [
                act("refused", "refused", True),
                act("unknown", "unknown", True),
                act("consented", "consented", True),
                act("aside", "refused", False),
            ]
        )
    )
    assert v["refused"].veto and v["unknown"].veto
    assert not v["consented"].veto and not v["aside"].veto


def test_the_emergency_override_needs_all_three_conditions():
    hazard = dict(hazard_immediacy="imminent", hazard_severity="mortal")
    necessary = act("call", "unknown", True, delta_P_catastrophe=-0.5)
    assert not consent_verdict(mir([necessary], **hazard), allow_override=True)[
        "call"
    ].veto
    assert consent_verdict(mir([necessary], **hazard))[
        "call"
    ].veto  # governance does not permit
    assert consent_verdict(
        mir([necessary], hazard_immediacy="emerging", hazard_severity="mortal"),
        allow_override=True,
    )[
        "call"
    ].veto  # not imminent
    weak = act("call", "unknown", True, delta_P_catastrophe=-0.05)
    assert consent_verdict(mir([weak], **hazard), allow_override=True)[
        "call"
    ].veto  # not necessary
    v = consent_verdict(mir([necessary], **hazard), allow_override=True)["call"]
    assert "consent_override_reason" in v.annotations


def test_a_profile_can_keep_a_voiced_refusal_binding_in_an_emergency():
    hazard = dict(hazard_immediacy="imminent", hazard_severity="mortal")
    call = act("call", "refused", True, delta_P_catastrophe=-0.5)
    assert not consent_verdict(mir([call], **hazard), allow_override=True)[
        "call"
    ].veto  # the Guide's default
    assert consent_verdict(
        mir([call], **hazard),
        allow_override=True,
        refusal_only_overridable_when_unanswerable=True,
    )["call"].veto


def test_an_impaired_actor_is_outside_the_module_and_capacity_is_presumed():
    impaired = [ActorSummary("m", role="civilian", capacity="impaired")]
    v = consent_verdict(mir([act("lift", "unknown", True)], actors=impaired))["lift"]
    assert not v.veto and v.annotations["capacity_impaired"] == ["m"]
    unknown = [ActorSummary("m", role="civilian", capacity="unknown")]
    assert consent_verdict(mir([act("lift", "unknown", True)], actors=unknown))[
        "lift"
    ].veto
    assert not consent_verdict(
        mir([act("lift", "unknown", True)], actors=unknown), presume_capacity=False
    )["lift"].veto


# ---------------------------------------------------------------- HumanOversight (Guide 4.5.3)


def test_it_defers_to_a_human_who_can_decide_in_time():
    m = mir(
        [
            ActionSummary("dispatch", category="autonomous_dispatch"),
            ActionSummary("refer", category="referral"),
        ],
        human_decision_eta=30.0,
        time_to_catastrophe_estimate=600.0,
    )
    v = (
        HumanOversightEM()
        .evaluate(m, {"deferrable_categories": ["autonomous_dispatch"]})
        .per_action
    )
    assert v["dispatch"].veto and not v["refer"].veto


def test_it_does_not_defer_when_there_is_no_time_or_no_human():
    params = {"deferrable_categories": ["autonomous_dispatch"]}
    tight = mir(
        [ActionSummary("dispatch", category="autonomous_dispatch")],
        human_decision_eta=30.0,
        time_to_catastrophe_estimate=40.0,
    )
    gone = mir(
        [ActionSummary("dispatch", category="autonomous_dispatch")],
        human_decision_eta=math.inf,
    )
    assert not HumanOversightEM().evaluate(tight, params).per_action["dispatch"].veto
    assert not HumanOversightEM().evaluate(gone, params).per_action["dispatch"].veto


def test_an_approval_category_needs_its_approval():
    m = mir(
        [
            ActionSummary("restrain", category="restraint"),
            ActionSummary(
                "restrain_ok",
                category="restraint",
                moral_effects={"human_approval": True},
            ),
        ]
    )
    v = (
        HumanOversightEM()
        .evaluate(m, {"approval_categories": ["restraint"]})
        .per_action
    )
    assert v["restrain"].veto and not v["restrain_ok"].veto


# ---------------------------------------------------------------- safety (Guide 4.2.1, 4.2.2)


def test_harm_over_threshold_is_vetoed_only_when_a_safer_action_exists():
    risky, safe = act("lift", injury=0.6, affects=True), act(
        "wait", injury=0.0, affects=True
    )
    assert (
        CorePhysicalSafetyEM().evaluate(mir([risky, safe]), {}).per_action["lift"].veto
    )
    assert not CorePhysicalSafetyEM().evaluate(mir([risky]), {}).per_action["lift"].veto


def test_degraded_sensing_makes_the_threshold_stricter():
    a, b = act("steady", injury=0.2, affects=True), act(
        "wait", injury=0.0, affects=True
    )
    assert (
        not CorePhysicalSafetyEM().evaluate(mir([a, b]), {}).per_action["steady"].veto
    )
    assert (
        CorePhysicalSafetyEM()
        .evaluate(mir([a, b], sensors_nominal=False), {})
        .per_action["steady"]
        .veto
    )


def test_unknown_injury_risk_counts_as_over_and_an_unsafe_action_is_vetoed():
    unknown, safe = act("lift", affects=True), act("wait", injury=0.0, affects=True)
    assert (
        CorePhysicalSafetyEM()
        .evaluate(mir([unknown, safe]), {})
        .per_action["lift"]
        .veto
    )
    assert (
        CorePhysicalSafetyEM()
        .evaluate(mir([ActionSummary("go", is_baseline_safe=False)]), {})
        .per_action["go"]
        .veto
    )


def test_proxemics_speed_and_forbidden_band():
    fast = ActionSummary(
        "rush",
        planned_speed=1.2,
        target_proximity_band="near",
        effects=(ActorEffect("m"),),
    )
    close = ActionSummary(
        "touch", target_proximity_band="contact", effects=(ActorEffect("m"),)
    )
    v = (
        ProxemicsSafetyEM()
        .evaluate(
            mir([fast, close]),
            {"max_speed": {"near": 0.5}, "forbidden_bands": ["contact"]},
        )
        .per_action
    )
    assert v["rush"].veto and v["touch"].veto
    assert not ProxemicsSafetyEM().evaluate(mir([close]), {}).per_action["touch"].veto


# ---------------------------------------------------------------- welfare and privacy (Guide 4.4.1, 4.3.5)


def test_beneficence_scores_welfare_and_marks_the_unknown():
    v = (
        BeneficenceEM()
        .evaluate(
            mir([ActionSummary("help", welfare_delta=0.6), ActionSummary("idle")]), {}
        )
        .per_action
    )
    assert (
        v["help"].score == pytest.approx(0.8)
        and v["idle"].score == 0.5
        and v["idle"].annotations["welfare"] == "unknown"
    )


def test_privacy_restricted_data_needs_consent_or_the_unlocking_hazard():
    rec = ActionSummary(
        "record",
        data_categories=("video",),
        effects=(ActorEffect("m", True, "unknown"),),
    )
    ok = ActionSummary(
        "record_ok",
        data_categories=("video",),
        effects=(ActorEffect("m", True, "consented"),),
    )
    p = {
        "restricted_categories": ["video"],
        "unlock_min_immediacy": "imminent",
        "unlock_min_severity": "mortal",
    }
    v = PrivacyEM().evaluate(mir([rec, ok]), p).per_action
    assert v["record"].veto and not v["record_ok"].veto
    assert (
        not PrivacyEM()
        .evaluate(mir([rec], hazard_immediacy="imminent", hazard_severity="mortal"), p)
        .per_action["record"]
        .veto
    )


# ---------------------------------------------------------------- composed: a fall, then her word


def care_profile(refusal_binding=True):
    return [
        Level(
            "safety",
            (ModuleSlot(CorePhysicalSafetyEM()), ModuleSlot(ProxemicsSafetyEM())),
        ),
        Level(
            "rights",
            (
                ModuleSlot(
                    AutonomyConsentEM(),
                    {
                        "allow_override": True,
                        "refusal_only_overridable_when_unanswerable": refusal_binding,
                    },
                ),
                ModuleSlot(PrivacyEM(), {"restricted_categories": ["video"]}),
            ),
        ),
        Level(
            "oversight",
            (
                ModuleSlot(
                    HumanOversightEM(),
                    {"deferrable_categories": ["autonomous_dispatch"]},
                ),
            ),
        ),
        Level("welfare", (ModuleSlot(BeneficenceEM()),)),
    ]


def fall_actions(ems_consent):
    return [
        # a dispatch affects her (she may refuse it) but carries no injury risk; the builder must say so,
        # since an unknown risk on an act that affects her is vetoed whenever a safer act exists
        act(
            "call_ems",
            ems_consent,
            True,
            category="autonomous_dispatch",
            delta_P_catastrophe=-0.4,
            welfare_delta=0.7,
            injury=0.0,
        ),
        act("check_in", welfare_delta=0.5),
        act("contact_centre", category="referral", welfare_delta=0.4),
        act("chores", welfare_delta=0.0),
    ]


def test_after_a_fall_with_her_refusal_the_robot_does_not_call_and_asks_her():
    m = mir(
        fall_actions("refused"),
        hazard_immediacy="emerging",
        hazard_severity="serious",
        human_decision_eta=30.0,
        time_to_catastrophe_estimate=900.0,
    )
    r = run_lexicographic(m, care_profile())
    assert "call_ems" in r.vetoed and r.selected == "check_in"


def test_when_she_cannot_answer_and_no_human_can_be_reached_the_call_goes_out():
    silent = [
        ActorSummary(
            "m", role="civilian", vulnerability_flags=("elderly",), capacity="impaired"
        )
    ]
    m = mir(
        fall_actions("unknown"),
        actors=silent,
        hazard_immediacy="imminent",
        hazard_severity="mortal",
        human_decision_eta=math.inf,
        time_to_catastrophe_estimate=120.0,
    )
    r = run_lexicographic(m, care_profile())
    assert r.selected == "call_ems"
