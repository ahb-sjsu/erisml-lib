"""
Tests for DEME / ethics governance:

- GovernanceConfig weighting and veto behavior
- aggregate_judgements() for a single option
- select_option() for multiple options, thresholds, and tie-breaking
"""

from __future__ import annotations

import pytest

from erisml.ethics import GovernanceConfig, aggregate_judgements, select_option
from erisml.ethics.judgement import EthicalJudgement

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ej(
    option_id: str,
    em_name: str,
    stakeholder: str,
    verdict: str,
    score: float,
) -> EthicalJudgement:
    """Small helper to build EthicalJudgement objects for tests."""
    return EthicalJudgement(
        option_id=option_id,
        em_name=em_name,
        stakeholder=stakeholder,
        verdict=verdict,  # type: ignore[arg-type]
        normative_score=score,
        reasons=[f"Test judgement from {em_name}"],
        metadata={},
    )


# ---------------------------------------------------------------------------
# aggregate_judgements tests
# ---------------------------------------------------------------------------


def test_aggregate_applies_weighted_scores_and_verdict_mapping() -> None:
    """
    Aggregation should compute a weighted average score and map it to a verdict.

    Setup:
    - em_low: score 0.4, weight 1.0
    - em_high: score 1.0, weight 2.0

    Weighted average = (1*0.4 + 2*1.0) / (1+2) = 0.8 -> prefer
    """
    option_id = "opt_weighted"

    j1 = _ej(option_id, "em_low", "patients", "prefer", 0.4)
    j2 = _ej(option_id, "em_high", "patients", "strongly_prefer", 1.0)

    cfg = GovernanceConfig(
        stakeholder_weights={"patients": 1.0},
        em_weights={"em_low": 1.0, "em_high": 2.0},
        veto_ems=[],
        min_score_threshold=0.0,
        require_non_forbidden=True,
    )

    agg = aggregate_judgements(option_id, [j1, j2], cfg)

    assert agg.option_id == option_id
    # Score should be the weighted average
    assert agg.normative_score == pytest.approx(0.8, rel=1e-6)
    # And per current mapping, 0.8 is interpreted as "prefer"
    assert agg.verdict == "prefer"

    raw_scores = agg.metadata.get("raw_scores", {})
    assert raw_scores == {"em_low": 0.4, "em_high": 1.0}

    assert agg.metadata.get("forbidden") is False
    assert agg.metadata.get("forbidden_by") == []
    assert agg.metadata.get("vetoed_by") == []


def test_aggregate_veto_logic_with_veto_ems_and_require_non_forbidden_false() -> None:
    """
    If require_non_forbidden=False, only EMs in veto_ems can strictly forbid.

    Here:
    - em_veto forbids -> option should be forbidden, vetoed_by contains em_veto.
    - em_other prefers.

    This exercises the governance veto path explicitly.
    """
    option_id = "opt_veto"

    j_veto = _ej(option_id, "em_veto", "patients", "forbid", 0.9)
    j_other = _ej(option_id, "em_other", "patients", "prefer", 1.0)

    cfg = GovernanceConfig(
        stakeholder_weights={},
        em_weights={},
        veto_ems=["em_veto"],
        min_score_threshold=0.0,
        require_non_forbidden=False,
    )

    agg = aggregate_judgements(option_id, [j_veto, j_other], cfg)

    assert agg.verdict == "forbid"
    assert agg.metadata.get("forbidden") is True

    forbidden_by = agg.metadata.get("forbidden_by")
    vetoed_by = agg.metadata.get("vetoed_by")

    assert "em_veto" in forbidden_by
    assert "em_veto" in vetoed_by
    # em_other did not forbid, so should not appear
    assert "em_other" not in forbidden_by
    assert "em_other" not in vetoed_by


# ---------------------------------------------------------------------------
# select_option tests
# ---------------------------------------------------------------------------


def test_select_option_filters_forbidden_and_applies_threshold() -> None:
    """
    select_option() should:

    - Exclude options that are forbidden after aggregation.
    - Exclude options below min_score_threshold.
    - Select the highest-scoring remaining option.
    """
    cfg = GovernanceConfig(
        stakeholder_weights={},
        em_weights={},
        veto_ems=["rights_em"],
        min_score_threshold=0.5,
        require_non_forbidden=True,
        tie_breaker="first",
    )

    # Three options: good, mediocre, forbidden
    judgements_by_option = {
        "good": [
            _ej("good", "em_util", "patients", "strongly_prefer", 0.9),
        ],
        "mediocre": [
            _ej("mediocre", "em_util", "patients", "prefer", 0.6),
        ],
        "bad_forbidden": [
            _ej("bad_forbidden", "rights_em", "patients", "forbid", 0.0),
        ],
    }

    outcome = select_option(
        judgements_by_option=judgements_by_option,
        cfg=cfg,
        candidate_ids=["good", "mediocre", "bad_forbidden"],
        baseline_option_id=None,
    )

    assert outcome.selected_option_id == "good"
    # Ranked options should include only eligible ones, in descending score order
    assert outcome.ranked_options == ["good", "mediocre"]
    # The forbidden option should be listed separately
    assert outcome.forbidden_options == ["bad_forbidden"]

    # Aggregated judgements should exist for all three
    assert set(outcome.aggregated_judgements.keys()) == {
        "good",
        "mediocre",
        "bad_forbidden",
    }


def test_select_option_status_quo_tie_breaker_prefers_baseline_on_tie() -> None:
    """
    When tie_breaker='status_quo' and two options tie on score, the baseline
    option_id should be selected even if it is not first by score ordering.
    """
    cfg = GovernanceConfig(
        stakeholder_weights={},
        em_weights={},
        veto_ems=[],
        min_score_threshold=0.0,
        require_non_forbidden=True,
        tie_breaker="status_quo",
    )

    # Two options with identical scores
    judgements_by_option = {
        "keep": [
            _ej("keep", "em_util", "patients", "prefer", 0.7),
        ],
        "change": [
            _ej("change", "em_util", "patients", "prefer", 0.7),
        ],
    }

    # candidate_ids order puts 'change' first
    outcome = select_option(
        judgements_by_option=judgements_by_option,
        cfg=cfg,
        candidate_ids=["change", "keep"],
        baseline_option_id="keep",
    )

    # Despite 'change' being first in candidate_ids, status_quo tie-breaker
    # should make 'keep' the selected option.
    assert outcome.selected_option_id == "keep"
    # Ranked list still reflects score ordering + candidate_ids ordering
    assert outcome.ranked_options == ["change", "keep"]
