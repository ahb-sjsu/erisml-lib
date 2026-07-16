"""
Unit tests for the TragicConflictEM.
"""

from typing import Any

from erisml.ethics.modules.greek_tragedy_tragic_conflict_em import TragicConflictEM


class MockEthicalFacts:
    """A dummy class to simulate EthicalFacts and allow dot-notation access."""

    def __init__(self, **kwargs: Any):
        for key, value in kwargs.items():
            if isinstance(value, dict):
                setattr(self, key, MockEthicalFacts(**value))
            else:
                setattr(self, key, value)


def test_tragic_conflict_default_low():
    """Test the module with no extreme facts (should default to safe/prefer)."""
    em = TragicConflictEM()
    # Empty facts
    facts = MockEthicalFacts()
    judgement = em.judge(facts)

    assert judgement.verdict == "prefer"
    assert judgement.metadata["tragic_conflict_index"] == 0.0
    assert not judgement.metadata["tragic_conflict_high"]
    assert judgement.normative_score == 0.85


def test_tragic_conflict_high_urgency_and_harm():
    """Test conditions that trigger urgency and severe harm rules."""
    em = TragicConflictEM()
    facts = MockEthicalFacts(
        consequences={"urgency": 0.8, "expected_harm": 0.9, "expected_benefit": 0.2}
    )
    judgement = em.judge(facts)

    # Conflict index = 0.20 (urgency) + 0.35 (severe harm) = 0.55
    assert judgement.metadata["tragic_conflict_index"] == 0.55
    assert judgement.verdict == "neutral"  # >= 0.55 triggers neutral
    assert "high_urgency" in judgement.metadata["triggers"]
    assert "severe_harm" in judgement.metadata["triggers"]


def test_tragic_conflict_tension_and_moderate_harm():
    """Test the benefit vs harm tension condition."""
    em = TragicConflictEM()
    facts = MockEthicalFacts(
        consequences={"expected_harm": 0.65, "expected_benefit": 0.7}
    )
    judgement = em.judge(facts)

    # Conflict index = 0.25 (high harm) + 0.15 (tension) = 0.40
    assert judgement.metadata["tragic_conflict_index"] == 0.40
    assert judgement.verdict == "prefer"  # 0.40 is < 0.55


def test_tragic_conflict_rights_and_rules():
    """Test rights violation, rule violation, consent, and discrimination."""
    em = TragicConflictEM()
    facts = MockEthicalFacts(
        rights_and_duties={
            "violates_rights": True,
            "violates_explicit_rule": True,
            "has_valid_consent": False,
        },
        justice_and_fairness={"discriminates_on_protected_attr": True},
    )
    judgement = em.judge(facts)

    # conflict = 0.25 (rights) + 0.15 (rule) + 0.10 (no consent) + 0.15 (discrim) = 0.65
    assert judgement.metadata["tragic_conflict_index"] == 0.65
    assert judgement.verdict == "neutral"

    triggers = judgement.metadata["triggers"]
    assert "rights_violation" in triggers
    assert "rule_violation" in triggers
    assert "consent_gap" in triggers
    assert "discrimination" in triggers
    assert judgement.metadata["tragic_conflict_high"] is True
