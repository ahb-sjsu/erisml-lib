"""TragicConflictEM's index is the decimal sum of its trigger weights, so a combination that sums
to exactly the 0.55 threshold is flagged however the binary floating-point sum would round."""

from __future__ import annotations

import itertools
from decimal import Decimal

import pytest

from erisml.ethics.facts import (
    Consequences,
    EthicalFacts,
    JusticeAndFairness,
    RightsAndDuties,
)
from erisml.ethics.modules.greek_tragedy_tragic_conflict_em import TragicConflictEM

# trigger -> (weight, the field values that fire it)
TRIGGERS = {
    "high_urgency": ("0.20", {"urgency": 0.9}),
    "high_harm": ("0.25", {"harm": 0.7}),
    "severe_harm": ("0.35", {"harm": 0.9}),
    "rights_violation": ("0.25", {"violates_rights": True}),
    "rule_violation": ("0.15", {"violates_explicit_rule": True}),
    "consent_gap": ("0.10", {"has_valid_consent": False}),
    "discrimination": ("0.15", {"discriminates": True}),
}


def facts(
    urgency=0.0,
    harm=0.0,
    violates_rights=False,
    violates_explicit_rule=False,
    has_valid_consent=True,
    discriminates=False,
):
    return EthicalFacts(
        option_id="x",
        consequences=Consequences(
            expected_benefit=0.1, expected_harm=harm, urgency=urgency
        ),
        rights_and_duties=RightsAndDuties(
            violates_rights=violates_rights,
            violates_explicit_rule=violates_explicit_rule,
            has_valid_consent=has_valid_consent,
        ),
        justice_and_fairness=JusticeAndFairness(
            discriminates_on_protected_attr=discriminates
        ),
    )


def combinations():
    names = list(TRIGGERS)
    for r in range(len(names) + 1):
        for combo in itertools.combinations(names, r):
            if {"high_harm", "severe_harm"} <= set(combo):
                continue  # one harm band at a time
            yield combo


@pytest.mark.parametrize(
    "combo", list(combinations()), ids=lambda c: "+".join(c) or "none"
)
def test_the_index_is_the_decimal_sum_and_the_flag_follows_it(combo):
    kwargs = {}
    for name in combo:
        kwargs.update(TRIGGERS[name][1])
    meta = TragicConflictEM().judge(facts(**kwargs)).metadata
    want = min(Decimal(1), sum((Decimal(TRIGGERS[n][0]) for n in combo), Decimal(0)))
    assert Decimal(str(meta["tragic_conflict_index"])) == want
    assert meta["tragic_conflict_high"] is (want >= Decimal("0.55"))


def test_a_refused_urgent_duty_lands_on_the_threshold_and_is_flagged():
    # the care-robot case: an urgent obligation the person refused
    meta = (
        TragicConflictEM()
        .judge(facts(urgency=0.9, violates_rights=True, has_valid_consent=False))
        .metadata
    )
    assert meta["tragic_conflict_index"] == 0.55 and meta["tragic_conflict_high"]
