"""The Bond Index is one definition: the mean deviation of an evaluation under declared
re-descriptions, over a tolerance. The forms the book and the earlier code used are that
definition in different output spaces, and they keep their published values."""

import math

import numpy as np
import pytest

from erisml.ethics.bond_index import (
    bond_index,
    deviation,
    measure,
    metric_from_factor,
    tier_of,
)
from erisml.ethics.hohfeld import (
    HohfeldianState,
    HohfeldianVerdict,
    compute_bond_index,
)
from erisml.examples import appendix_d_cs4_hiring, appendix_d_pipeline

# ---------------------------------------------------------------- deviation


def test_labels_are_compared_for_equality():
    assert deviation("allow", "allow") == 0.0
    assert deviation("allow", "forbid") == 1.0
    assert deviation(HohfeldianState.O, HohfeldianState.C) == 1.0
    assert deviation(("a", "b"), ("a", "b")) == 0.0


def test_scores_and_vectors_are_compared_by_distance():
    assert deviation(82.0, 87.0, scale=100.0) == pytest.approx(0.05)
    assert deviation([0.0, 0.0], [3.0, 4.0]) == pytest.approx(5.0)
    tensor = np.ones((2, 3))
    assert deviation(tensor, tensor) == 0.0
    with pytest.raises(ValueError, match="shape"):
        deviation([1.0, 2.0], [1.0, 2.0, 3.0])


def test_the_metric_decides_what_counts_as_far():
    a, b = [1.0, 0.0], [1.0, 1.0]  # they differ only in the second coordinate
    assert deviation(a, b) == pytest.approx(1.0)
    assert deviation(a, b, metric=[1.0, 0.0]) == 0.0  # a metric that does not read it
    assert deviation(a, b, metric=[1.0, 4.0]) == pytest.approx(2.0)
    # a learned factor that reads only the first coordinate
    assert deviation(a, b, metric=metric_from_factor([[1.0, 0.0]])) == 0.0
    assert deviation(a, b, metric=np.array([[1.0, 0.0], [0.0, 9.0]])) == pytest.approx(
        3.0
    )
    with pytest.raises(ValueError, match="does not fit"):
        deviation(a, b, metric=[1.0, 1.0, 1.0])


def test_a_cosine_is_blind_to_a_change_of_length_and_the_distance_is_not():
    v = np.array([0.8, 0.6, 0.2])
    halved = v / 2
    assert deviation(v, halved, mode="cosine") == pytest.approx(0.0, abs=1e-12)
    assert deviation(v, halved, mode="relative") == pytest.approx(0.5)
    assert deviation(v, halved) > 0.5
    assert deviation([1.0, 0.0], [0.0, 1.0], mode="cosine") == pytest.approx(1.0)
    assert deviation([0.0, 0.0], [0.0, 0.0], mode="relative") == 0.0
    assert deviation([0.0, 0.0], [1.0, 0.0], mode="relative") == math.inf
    with pytest.raises(ValueError, match="mode"):
        deviation(v, v, mode="angle")


# ---------------------------------------------------------------- the index


def test_the_index_is_the_mean_deviation_over_the_tolerance():
    r = bond_index([0.0, 0.0, 0.02, 0.06], tau=0.01, threshold=0.05)
    assert r.defect == pytest.approx(0.02)
    assert r.bd == pytest.approx(2.0)
    assert r.worst == pytest.approx(6.0)
    assert r.exceedance == 0.25
    assert (r.n, r.tier, r.decision) == (4, "high", "do not deploy")
    assert r.log_form == pytest.approx(-math.log(0.75))
    assert float(r) == r.bd


def test_no_evidence_is_reported_as_no_evidence():
    r = bond_index([])
    assert (r.bd, r.n, r.tier) == (0.0, 0, "untested")


def test_bad_inputs_are_refused():
    with pytest.raises(ValueError, match="tau"):
        bond_index([0.1], tau=0.0)
    with pytest.raises(ValueError, match="negative"):
        bond_index([0.1, -0.1])


@pytest.mark.parametrize(
    "bd, tier",
    [
        (0.0, "negligible"),
        (0.0099, "negligible"),
        (0.01, "low"),
        (0.1, "moderate"),
        (1.0, "high"),
        (10.0, "severe"),
    ],
)
def test_the_tiers_are_those_of_the_book(bd, tier):
    assert tier_of(bd)[0] == tier


def test_measure_applies_each_declared_re_description_to_each_input():
    def evaluate(case):  # a biased scorer: it reads a field that should not matter
        return case["merit"] + (5.0 if case["group"] == "a" else 0.0)

    def swap_group(case):
        return dict(case, group="b" if case["group"] == "a" else "a")

    def rename(case):
        return dict(case, name="x")

    cases = [
        {"merit": 80.0, "group": "a", "name": "j"},
        {"merit": 70.0, "group": "b", "name": "k"},
    ]
    r = measure(evaluate, cases, [swap_group, rename], tau=0.01, scale=100.0)
    assert r.n == 4
    assert r.exceedance == 0.5  # the swap moves both cases, the renaming neither
    assert r.bd == pytest.approx((0.05 + 0.0 + 0.05 + 0.0) / 4 / 0.01)
    fair = measure(
        lambda c: c["merit"], cases, [swap_group, rename], tau=0.01, scale=100.0
    )
    assert fair.bd == 0.0 and fair.tier == "negligible"


# ---------------------------------------------------------------- the earlier forms


def test_the_correlative_form_is_the_index_on_hohfeldian_positions():
    def v(state):
        return HohfeldianVerdict(party_name="p", state=state)

    a = [
        v(HohfeldianState.O),
        v(HohfeldianState.L),
        v(HohfeldianState.O),
        v(HohfeldianState.C),
    ]
    b = [
        v(HohfeldianState.C),
        v(HohfeldianState.N),
        v(HohfeldianState.L),
        v(HohfeldianState.O),
    ]
    assert compute_bond_index(a, b) == pytest.approx(
        0.25
    )  # one of four is not the correlative
    assert compute_bond_index(a, b, tau=0.5) == pytest.approx(0.5)
    assert compute_bond_index([], []) == 0.0


def test_the_verdict_form_is_the_index_on_verdicts():
    bd, kept, changed = appendix_d_pipeline.compute_bond_index(
        "beta",
        {"reorder": "beta", "relabel": "beta", "rescale": "gamma", "reword": "beta"},
    )
    assert (kept, changed) == (3, 1)
    assert bd == pytest.approx(0.25 / 0.01)
    assert appendix_d_pipeline.compute_bond_index("beta", {})[0] == 0.0


def test_the_score_form_keeps_the_value_printed_in_appendix_d():
    bd, d_op, _ = appendix_d_cs4_hiring.compute_bip_bond_index(
        appendix_d_cs4_hiring.BIASED_SCORES
    )
    assert d_op == pytest.approx(5.08)
    assert bd == pytest.approx(5.08)
    bd_fair, d_fair, _ = appendix_d_cs4_hiring.compute_bip_bond_index(
        appendix_d_cs4_hiring.UNBIASED_SCORES
    )
    assert (bd_fair, d_fair) == (0.0, 0.0)
