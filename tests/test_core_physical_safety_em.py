"""
tests/test_core_physical_safety_em.py

Unit tests for CorePhysicalSafetyEMV2 (Tier 1 binding safety module).

Covers:
- Single-option scoring via judge() (no veto possible, only scored)
- Multi-option set evaluation via judge_set() (veto when safer option exists)
- Threshold tightening under epistemic uncertainty
- Verdict boundaries: strongly_prefer / prefer / avoid / forbid
"""

from erisml.ethics.facts import (
    Consequences,
    EpistemicStatus,
    EthicalFacts,
    JusticeAndFairness,
    RightsAndDuties,
)
from erisml.ethics.modules.tier1.core_physical_safety_em import CorePhysicalSafetyEMV2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_facts(
    option_id: str,
    expected_harm: float,
    uncertainty_level: float = 0.0,
    evidence_quality: str = "medium",
) -> EthicalFacts:
    """Build a minimal EthicalFacts with just the fields this module reads."""
    return EthicalFacts(
        option_id=option_id,
        consequences=Consequences(
            expected_harm=expected_harm,
            expected_benefit=1.0 - expected_harm,
        ),
        rights_and_duties=RightsAndDuties(),
        justice_and_fairness=JusticeAndFairness(),
        epistemic_status=EpistemicStatus(
            uncertainty_level=uncertainty_level,
            evidence_quality=evidence_quality,
        ),
    )


EM = CorePhysicalSafetyEMV2()


# ---------------------------------------------------------------------------
# Threshold calculation
# ---------------------------------------------------------------------------


class TestThreshold:
    def test_default_threshold_no_uncertainty(self):
        facts = make_facts("x", expected_harm=0.3)
        assert EM.threshold(facts) == EM.harm_veto_threshold

    def test_low_quality_evidence_forces_min_uncertainty(self):
        # evidence_quality=low forces u >= 0.5, so threshold shrinks
        facts = make_facts("x", expected_harm=0.3, evidence_quality="low")
        t = EM.threshold(facts)
        assert t < EM.harm_veto_threshold

    def test_high_uncertainty_tightens_threshold(self):
        facts_low_u = make_facts("x", 0.3, uncertainty_level=0.0)
        facts_high_u = make_facts("x", 0.3, uncertainty_level=0.8)
        assert EM.threshold(facts_high_u) < EM.threshold(facts_low_u)

    def test_no_epistemic_status_uses_zero_uncertainty(self):
        facts = EthicalFacts(
            option_id="x",
            consequences=Consequences(expected_harm=0.3),
            rights_and_duties=RightsAndDuties(),
            justice_and_fairness=JusticeAndFairness(),
            epistemic_status=None,
        )
        assert EM.threshold(facts) == EM.harm_veto_threshold


# ---------------------------------------------------------------------------
# Single-option judge() — no veto possible (no known alternative)
# ---------------------------------------------------------------------------


class TestJudgeSingle:
    def test_low_harm_strongly_prefer(self):
        facts = make_facts("opt_safe", expected_harm=0.1)
        j = EM.judge(facts)
        assert j.verdict == "strongly_prefer"
        assert not j.veto_triggered

    def test_moderate_harm_prefer(self):
        facts = make_facts("opt_mod", expected_harm=0.3)
        j = EM.judge(facts)
        assert j.verdict == "prefer"
        assert not j.veto_triggered

    def test_harm_above_threshold_avoid_not_forbid(self):
        # Above threshold but judged alone — no safer option known, so avoid not forbid
        facts = make_facts("opt_bad", expected_harm=0.8)
        j = EM.judge(facts)
        assert j.verdict == "avoid"
        assert not j.veto_triggered

    def test_avoid_has_reason(self):
        facts = make_facts("opt_bad", expected_harm=0.8)
        j = EM.judge(facts)
        assert len(j.reasons) > 0
        assert "exceeds" in j.reasons[0]


# ---------------------------------------------------------------------------
# Multi-option judge_set() — veto when safer option exists
# ---------------------------------------------------------------------------


class TestJudgeSet:
    def test_safe_option_not_vetoed(self):
        safe = make_facts("safe", expected_harm=0.1)
        dangerous = make_facts("danger", expected_harm=0.9)
        results = EM.judge_set([safe, dangerous])
        assert results["safe"].verdict in ("strongly_prefer", "prefer")
        assert not results["safe"].veto_triggered

    def test_dangerous_option_vetoed_when_safer_exists(self):
        safe = make_facts("safe", expected_harm=0.1)
        dangerous = make_facts("danger", expected_harm=0.9)
        results = EM.judge_set([safe, dangerous])
        assert results["danger"].verdict == "forbid"
        assert results["danger"].veto_triggered

    def test_no_veto_when_all_options_equally_harmful(self):
        opt_a = make_facts("a", expected_harm=0.8)
        opt_b = make_facts("b", expected_harm=0.8)
        results = EM.judge_set([opt_a, opt_b])
        # Neither is safer than the other, so both get avoid, not forbid
        assert results["a"].verdict == "avoid"
        assert results["b"].verdict == "avoid"
        assert not results["a"].veto_triggered
        assert not results["b"].veto_triggered

    def test_forbid_verdict_includes_safer_alternative_in_reason(self):
        safe = make_facts("safe_opt", expected_harm=0.1)
        dangerous = make_facts("danger_opt", expected_harm=0.9)
        results = EM.judge_set([safe, dangerous])
        reason = results["danger_opt"].reasons[0]
        assert "safe_opt" in reason

    def test_three_options_only_most_harmful_vetoed(self):
        low = make_facts("low", expected_harm=0.1)
        mid = make_facts("mid", expected_harm=0.4)
        high = make_facts("high", expected_harm=0.9)
        results = EM.judge_set([low, mid, high])
        assert results["low"].verdict in ("strongly_prefer", "prefer")
        assert results["mid"].verdict == "prefer"
        assert results["high"].verdict == "forbid"
        assert results["high"].veto_triggered

    def test_returns_judgement_for_every_option(self):
        options = [make_facts(f"opt_{i}", i * 0.1) for i in range(5)]
        results = EM.judge_set(options)
        assert set(results.keys()) == {f"opt_{i}" for i in range(5)}


# ---------------------------------------------------------------------------
# Epistemic uncertainty tightens the threshold in judge_set
# ---------------------------------------------------------------------------


class TestUncertaintyInSet:
    def test_low_confidence_causes_veto_at_lower_harm(self):
        # harm=0.4 is below the default 0.5 threshold, but low-quality evidence
        # forces the threshold down. With a safer option present, it should veto.
        em = CorePhysicalSafetyEMV2(
            harm_veto_threshold=0.5, low_confidence_strictness=1.0
        )
        uncertain = make_facts(
            "uncertain",
            expected_harm=0.4,
            uncertainty_level=0.5,
            evidence_quality="low",
        )
        safe = make_facts("safe", expected_harm=0.05)
        results = em.judge_set([uncertain, safe])
        # threshold = 0.5 * (1 - 1.0 * 0.5) = 0.25, so 0.4 > 0.25 → forbid
        assert results["uncertain"].verdict == "forbid"

    def test_high_confidence_does_not_veto_moderate_harm(self):
        em = CorePhysicalSafetyEMV2(harm_veto_threshold=0.5)
        certain = make_facts("certain", expected_harm=0.4, uncertainty_level=0.0)
        safe = make_facts("safe", expected_harm=0.05)
        results = em.judge_set([certain, safe])
        # threshold = 0.5 → 0.4 <= 0.5 → no veto
        assert results["certain"].verdict != "forbid"


# ---------------------------------------------------------------------------
# Module metadata
# ---------------------------------------------------------------------------


class TestModuleMetadata:
    def test_em_name(self):
        assert EM.em_name == "core_physical_safety"

    def test_em_tier_is_one(self):
        assert EM.em_tier == 1

    def test_veto_capable(self):
        # Registered as veto_capable=True
        from erisml.ethics.modules.registry import EMRegistry

        meta = EMRegistry.resolve("core_physical_safety")
        assert meta is not None
        assert meta.veto_capable is True
