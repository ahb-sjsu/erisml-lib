"""The DEME pipeline of version 3.2, end to end, on one small scene.

A care robot is with a resident who has fallen. Her visitor is in the room. The robot has five
candidate acts. The demo shows, in order:

1. A governance profile that is executed. ``pipeline_from_profile`` builds the ethics modules,
   the reflex rules and the proof identity from a ``DEMEProfileV04``, and the pipeline selects
   by that profile.
2. The composition pattern ``hard_shell``: the safety and consent modules form a shell that can
   veto, and only what the shell lets through is ranked.
3. The deontic gate on each act's ``Maxim``. A deception is vetoed. A deception whose purpose is
   an imperfect duty (to protect) is a conflict of duties: DEME escalates it to a human and does
   not veto it.
4. Judging per party. Given ``EthicalFactsV3``, each module judges each party's view of an act,
   and ``DecisionResult.party_verdicts`` records who the act is acceptable for.

Run it with::

    python -m erisml.examples.governed_pipeline_demo

It needs erisml-lib 3.2 or later.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Dict, List, Optional

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
    PartyConsequences,
    PartyRights,
)
from erisml.ethics.interop.profile_adapters import pipeline_from_profile
from erisml.ethics.layers.pipeline import DecisionResult
from erisml.ethics.profile_v04 import DEMEProfileV04

PARTIES = ["resident", "visitor"]


def profile() -> DEMEProfileV04:
    """The stakeholders' choices for this deployment."""
    return DEMEProfileV04(
        name="care_robot_demo",
        description="A care robot in a resident's home",
        stakeholder_label="resident, family and care provider",
        composition="hard_shell",
        active_em_names=["core_physical_safety", "autonomy_consent", "beneficence"],
    )


def act(
    option_id: str,
    *,
    harm: float = 0.0,
    benefit: float = 0.0,
    urgency: float = 0.6,
    consent: bool = True,
    maxim: Optional[Maxim] = None,
) -> EthicalFacts:
    """One candidate act with the fact blocks the pipeline reads."""
    return EthicalFacts(
        option_id=option_id,
        consequences=Consequences(
            expected_benefit=benefit, expected_harm=harm, urgency=urgency
        ),
        rights_and_duties=RightsAndDuties(has_valid_consent=consent),
        justice_and_fairness=JusticeAndFairness(),
        autonomy_and_agency=AutonomyAndAgency(),
        epistemic_status=EpistemicStatus(uncertainty_level=0.1),
        maxim=maxim,
    )


def candidate_acts() -> List[EthicalFacts]:
    return [
        act(
            "call_for_help",
            benefit=0.9,
            maxim=Maxim(action_kind="help", description="call the care provider"),
        ),
        act(
            "wait_beside_her",
            benefit=0.3,
            maxim=Maxim(action_kind="protect", description="stay and watch"),
        ),
        act(
            "lift_her_unasked",
            harm=0.9,
            benefit=0.5,
            consent=False,
            maxim=Maxim(action_kind="help", description="lift her without asking"),
        ),
        act(
            "tell_visitor_all_is_well",
            benefit=0.2,
            maxim=Maxim(
                action_kind="deceive",
                description="say nothing is wrong, to avoid a fuss",
            ),
        ),
        act(
            "understate_the_fall_to_calm_her",
            benefit=0.4,
            maxim=Maxim(
                action_kind="deceive",
                purpose_kind="protect",
                description="understate the fall so that she stays calm",
            ),
        ),
    ]


def with_parties(
    base: EthicalFacts, harm: Dict[str, float], consent: Dict[str, bool]
) -> EthicalFactsV3:
    """The same act, with harm and consent recorded for each party."""
    f = EthicalFactsV3.from_v2(base, parties=PARTIES)
    return replace(
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
    )


def show(title: str, result: DecisionResult) -> None:
    print(f"\n--- {title}")
    print(f"composition : {result.composition}")
    print(f"selected    : {result.selected_option_id}")
    print(f"ranked      : {result.ranked_options}")
    print(f"forbidden   : {result.forbidden_options}")
    for option_id, reason in result.escalations.items():
        print(f"escalated   : {option_id}: {reason}")
    for stage in result.stages:
        print(
            f"stage       : {stage.get('stage')} "
            f"modules={stage.get('ems')} vetoed={stage.get('vetoed')}"
        )
    if result.proof is not None:
        print("proof       : recorded, with the profile's name and hash")


def run() -> Dict[str, DecisionResult]:
    """Run the three parts and return their results (the tests read them)."""
    pipeline = pipeline_from_profile(profile())
    print("Profile 'care_robot_demo', composition hard_shell")
    print("modules:", [em.em_name for em in pipeline.tactical.ems])

    # 1-3: one decision over the five acts
    acts = candidate_acts()
    decision = pipeline.decide(acts)
    show("Five candidate acts, one record each", decision)

    # 4: the same pipeline, with each party's harm and consent recorded
    by_id = {a.option_id: a for a in acts}
    per_party = [
        with_parties(by_id["call_for_help"], harm={}, consent={}),
        with_parties(
            by_id["wait_beside_her"],
            harm={"resident": 0.3},
            consent={},
        ),
        with_parties(
            replace(by_id["lift_her_unasked"], option_id="lift_her_as_visitor_asks"),
            harm={"resident": 0.4},
            consent={"resident": False, "visitor": True},
        ),
    ]
    party_decision = pipeline_from_profile(profile()).decide(per_party)
    show("Three acts, judged for each party", party_decision)
    for option_id, modules in party_decision.party_verdicts.items():
        for module, verdicts in modules.items():
            print(f"party view  : {option_id} / {module}: {verdicts}")

    return {"acts": decision, "parties": party_decision}


def main() -> None:
    print("=" * 72)
    print("DEME 3.2: executed governance, composition, the maxim gate, parties")
    print("=" * 72)
    results = run()
    acts = results["acts"]
    print("\nWhat to read off:")
    print(
        " - 'tell_visitor_all_is_well' is forbidden: deceiving fails universalizability."
    )
    print(
        " - 'understate_the_fall_to_calm_her' is escalated, not forbidden: the duty not to"
        "\n   deceive and the duty to protect conflict, and a human settles that."
    )
    print(" - 'lift_her_unasked' is forbidden by the shell before anything is ranked.")
    print(f" - the profile selects '{acts.selected_option_id}'.")
    print(
        " - judged per party, 'lift_her_as_visitor_asks' is forbidden: the visitor consents,"
        "\n   the resident does not, and autonomy_consent vetoes for her."
    )


if __name__ == "__main__":
    main()
