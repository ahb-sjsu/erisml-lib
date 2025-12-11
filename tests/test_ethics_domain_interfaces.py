"""
Tests for domain & assessment interfaces:

- CandidateOption
- DomainAssessmentContext
- build_facts_for_options

We use small fake EthicalFactsBuilder implementations to verify that:

- Facts are built and keyed correctly by option_id.
- Options that raise ValueError are skipped.
- A mismatch between CandidateOption.option_id and EthicalFacts.option_id
  triggers a ValueError.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pytest

from erisml.ethics import (
    EthicalFacts,
    Consequences,
    RightsAndDuties,
    JusticeAndFairness,
)
from erisml.ethics.domain.interfaces import (
    CandidateOption,
    DomainAssessmentContext,
    EthicalFactsBuilder,
    build_facts_for_options,
)


@dataclass
class _EchoFactsBuilder:
    """
    Simple EthicalFactsBuilder used for tests.

    - Uses option.option_id as the EthicalFacts.option_id.
    - Uses a trivial, fixed mapping for all ethical dimensions.
    - Tracks which options were seen via 'seen_ids'.
    """

    seen_ids: List[str]

    def build_facts(
        self,
        option: CandidateOption,
        context: DomainAssessmentContext,
    ) -> EthicalFacts:
        self.seen_ids.append(option.option_id)

        # Simple, fixed mapping that ignores the details of context and payload.
        return EthicalFacts(
            option_id=option.option_id,
            consequences=Consequences(
                expected_benefit=0.5,
                expected_harm=0.1,
                urgency=0.3,
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
                prioritizes_most_disadvantaged=False,
                distributive_pattern=None,
                exploits_vulnerable_population=False,
                exacerbates_power_imbalance=False,
            ),
            # Optional blocks are omitted (None) for this minimal test builder.
            autonomy_and_agency=None,
            privacy_and_data=None,
            societal_and_environmental=None,
            virtue_and_care=None,
            procedural_and_legitimacy=None,
            epistemic_status=None,
            tags=["echo"],
            extra={"payload_type": type(option.payload).__name__},
        )


class _MismatchedIdBuilder:
    """
    Builder that intentionally returns an EthicalFacts option_id that does
    NOT match CandidateOption.option_id, to exercise the mismatch error.
    """

    def build_facts(
        self,
        option: CandidateOption,
        context: DomainAssessmentContext,
    ) -> EthicalFacts:
        return EthicalFacts(
            option_id=option.option_id + "_WRONG",
            consequences=Consequences(
                expected_benefit=0.5,
                expected_harm=0.1,
                urgency=0.3,
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
                prioritizes_most_disadvantaged=False,
                distributive_pattern=None,
                exploits_vulnerable_population=False,
                exacerbates_power_imbalance=False,
            ),
        )


class _SelectiveBuilder:
    """
    Builder that raises ValueError for some options to test that
    build_facts_for_options() gracefully skips them.
    """

    def build_facts(
        self,
        option: CandidateOption,
        context: DomainAssessmentContext,
    ) -> EthicalFacts:
        # Skip options whose ID starts with "skip"
        if option.option_id.startswith("skip"):
            raise ValueError("Intentional skip for test")

        return EthicalFacts(
            option_id=option.option_id,
            consequences=Consequences(
                expected_benefit=0.7,
                expected_harm=0.2,
                urgency=0.5,
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
                prioritizes_most_disadvantaged=False,
                distributive_pattern=None,
                exploits_vulnerable_population=False,
                exacerbates_power_imbalance=False,
            ),
        )


def test_build_facts_for_options_basic_flow() -> None:
    """
    build_facts_for_options() should:

    - Call builder.build_facts() for each option.
    - Return a dict keyed by option_id.
    """
    options = [
        CandidateOption("opt_a", payload={"x": 1}),
        CandidateOption("opt_b", payload={"x": 2}),
        CandidateOption("opt_c", payload={"x": 3}),
    ]
    ctx = DomainAssessmentContext(state={"dummy": True})

    builder = _EchoFactsBuilder(seen_ids=[])
    facts_by_id = build_facts_for_options(builder, options, ctx)

    assert set(facts_by_id.keys()) == {"opt_a", "opt_b", "opt_c"}
    assert builder.seen_ids == ["opt_a", "opt_b", "opt_c"]

    # Spot-check one of the constructed facts
    fa = facts_by_id["opt_a"]
    assert fa.option_id == "opt_a"
    assert fa.consequences.expected_benefit == 0.5
    assert fa.rights_and_duties.violates_rights is False
    assert fa.extra is not None
    assert fa.extra.get("payload_type") == "dict"


def test_build_facts_for_options_skips_failed_options() -> None:
    """
    If builder.build_facts() raises ValueError for an option, that option
    should be skipped while others are still processed.
    """
    options = [
        CandidateOption("ok_1", payload=None),
        CandidateOption("skip_this", payload=None),
        CandidateOption("ok_2", payload=None),
    ]
    ctx = DomainAssessmentContext(state={})

    builder = _SelectiveBuilder()
    facts_by_id = build_facts_for_options(builder, options, ctx)

    assert set(facts_by_id.keys()) == {"ok_1", "ok_2"}
    assert "skip_this" not in facts_by_id


def test_build_facts_for_options_detects_id_mismatch() -> None:
    """
    If a builder returns EthicalFacts with an option_id that does not match
    CandidateOption.option_id, build_facts_for_options() should raise a
    ValueError.
    """
    options = [
        CandidateOption("opt_mismatch", payload=None),
    ]
    ctx = DomainAssessmentContext(state={})

    builder: EthicalFactsBuilder = _MismatchedIdBuilder()  # type: ignore[assignment]

    with pytest.raises(ValueError):
        _ = build_facts_for_options(builder, options, ctx)
