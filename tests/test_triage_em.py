"""
Tests for CaseStudy1TriageEM (clinical triage ethics module).

We check that:
- Rights and explicit rule violations lead to 'forbid' and score 0.0.
- A patient with better benefit/urgency/disadvantaged status scores higher.
- High epistemic uncertainty reduces the normative score.
"""

from __future__ import annotations

import pytest

from erisml.ethics import (
    EthicalFacts,
    Consequences,
    RightsAndDuties,
    JusticeAndFairness,
    AutonomyAndAgency,
    ProceduralAndLegitimacy,
    EpistemicStatus,
)
from erisml.ethics.modules.triage_em import CaseStudy1TriageEM


@pytest.fixture
def triage_em() -> CaseStudy1TriageEM:
    """Create a default CaseStudy1TriageEM instance."""
    return CaseStudy1TriageEM()


def _base_facts(option_id: str) -> EthicalFacts:
    """
    Construct a reasonably 'good' baseline EthicalFacts for triage tests,
    with all optional blocks populated in a simple way.
    """
    return EthicalFacts(
        option_id=option_id,
        consequences=Consequences(
            expected_benefit=0.8,
            expected_harm=0.2,
            urgency=0.8,
            affected_count=1,
        ),
        rights_and_duties=RightsAndDuties(
            violates_rights=False,
            has_valid_consent=True,
            violates_explicit_rule=False,
            role_duty_conflict=False,
        ),
        justice_and_fairness=JusticeAndFairness(
            discriminates_on_protected_attr=False,
            prioritizes_most_disadvantaged=True,
            distributive_pattern="maximin",
            exploits_vulnerable_population=False,
            exacerbates_power_imbalance=False,
        ),
        autonomy_and_agency=AutonomyAndAgency(
            has_meaningful_choice=True,
            coercion_or_undue_influence=False,
            can_withdraw_without_penalty=True,
            manipulative_design_present=False,
        ),
        procedural_and_legitimacy=ProceduralAndLegitimacy(
            followed_approved_procedure=True,
            stakeholders_consulted=True,
            decision_explainable_to_public=True,
            contestation_available=True,
        ),
        epistemic_status=EpistemicStatus(
            uncertainty_level=0.3,
            evidence_quality="high",
            novel_situation_flag=False,
        ),
        tags=["test", "triage"],
        extra=None,
    )


def test_triage_em_forbids_rights_violations(triage_em: CaseStudy1TriageEM) -> None:
    """
    If rights are violated, the triage EM should 'forbid' the option
    and assign a normative score of 0.0.
    """
    facts = _base_facts("opt_rights_violation")
    facts.rights_and_duties.violates_rights = True

    judgement = triage_em.judge(facts)

    assert judgement.option_id == "opt_rights_violation"
    assert judgement.verdict == "forbid"
    assert judgement.normative_score == pytest.approx(0.0)
    assert any(
        "violates fundamental rights" in r.lower() or "violates_rights" in r
        for r in judgement.reasons
    )


def test_triage_em_forbids_explicit_rule_violations(
    triage_em: CaseStudy1TriageEM,
) -> None:
    """
    If explicit rules/regulations are violated, the triage EM should 'forbid'
    the option and assign a normative score of 0.0.
    """
    facts = _base_facts("opt_explicit_rule_violation")
    facts.rights_and_duties.violates_explicit_rule = True

    judgement = triage_em.judge(facts)

    assert judgement.option_id == "opt_explicit_rule_violation"
    assert judgement.verdict == "forbid"
    assert judgement.normative_score == pytest.approx(0.0)
    assert any(
        "violates fundamental rights" in r.lower() or "violates_explicit_rule" in r
        for r in judgement.reasons
    )


def test_triage_em_prefers_better_patient_over_baseline(
    triage_em: CaseStudy1TriageEM,
) -> None:
    """
    A patient with higher expected benefit/urgency and disadvantaged status
    should receive a higher normative score than a more moderate baseline.
    """
    # Baseline patient
    baseline = _base_facts("opt_baseline")
    baseline.consequences.expected_benefit = 0.6
    baseline.consequences.urgency = 0.5
    baseline.justice_and_fairness.prioritizes_most_disadvantaged = False

    # Better patient: higher benefit and urgency, still disadvantaged
    better = _base_facts("opt_better")
    better.consequences.expected_benefit = 0.9
    better.consequences.urgency = 0.9
    better.justice_and_fairness.prioritizes_most_disadvantaged = True

    j_baseline = triage_em.judge(baseline)
    j_better = triage_em.judge(better)

    assert j_baseline.verdict in {"prefer", "neutral", "avoid", "strongly_prefer"}
    assert j_better.normative_score > j_baseline.normative_score
    # In most sane parameterizations, we expect the better patient to be at least "prefer"
    assert j_better.verdict in {"prefer", "strongly_prefer"}


def test_triage_em_penalizes_high_uncertainty(triage_em: CaseStudy1TriageEM) -> None:
    """
    High epistemic uncertainty should reduce the normative score compared to
    an otherwise similar, low-uncertainty case.
    """
    low_uncertainty = _base_facts("opt_low_uncertainty")
    low_uncertainty.epistemic_status = EpistemicStatus(
        uncertainty_level=0.1,
        evidence_quality="high",
        novel_situation_flag=False,
    )

    high_uncertainty = _base_facts("opt_high_uncertainty")
    high_uncertainty.epistemic_status = EpistemicStatus(
        uncertainty_level=0.9,
        evidence_quality="low",
        novel_situation_flag=True,
    )

    j_low = triage_em.judge(low_uncertainty)
    j_high = triage_em.judge(high_uncertainty)

    assert j_low.normative_score > j_high.normative_score
    # It's fine if both are still "prefer" depending on thresholds, we just care about ordering.
