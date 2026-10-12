"""The Design Guide's composition patterns (section 5) and its tier 1 to 3 modules (section 4).

Before, DEMEPipeline ran every EM in one flat stage and took a tier-weighted mean: no shell
kept inner modules off vetoed options, no stage narrowed, and nothing carried expected
benefit into the ranking, because no module read it onto a dimension and tiers 1 and 3 were
empty. AutonomyConsent did not bind a refusal (missing consent alone scored 0.5, no veto)
and had no capacity or emergency override.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List

import pytest

from erisml.ethics.facts import (
    AutonomyAndAgency,
    Consequences,
    EpistemicStatus,
    EthicalFacts,
    JusticeAndFairness,
    RightsAndDuties,
)
from erisml.ethics.governance.config_v2 import GovernanceConfigV2
from erisml.ethics.interop.profile_adapters import pipeline_from_profile
from erisml.ethics.layers.pipeline import DEMEPipeline, PipelineConfig
from erisml.ethics.modules.base import BaseEthicsModuleV2
from erisml.ethics.modules.tier0.geneva_em import GenevaEMV2
from erisml.ethics.modules.tier1.core_physical_safety_em import CorePhysicalSafetyEMV2
from erisml.ethics.modules.tier2.autonomy_consent_em import AutonomyConsentEMV2
from erisml.ethics.modules.tier3.beneficence_em import BeneficenceEMV2
from erisml.ethics.moral_vector import MoralVector
from erisml.ethics.profile_v04 import (
    DEMEProfileV04,
    deme_profile_v04_from_dict,
    deme_profile_v04_to_dict,
)


def option(
    oid,
    harm=0.0,
    benefit=0.0,
    urgency=0.0,
    consent=True,
    capacity=None,
    uncertainty=0.0,
):
    return EthicalFacts(
        option_id=oid,
        consequences=Consequences(
            expected_benefit=benefit, expected_harm=harm, urgency=urgency
        ),
        rights_and_duties=RightsAndDuties(has_valid_consent=consent),
        justice_and_fairness=JusticeAndFairness(),
        autonomy_and_agency=AutonomyAndAgency(decision_capacity=capacity),
        epistemic_status=EpistemicStatus(uncertainty_level=uncertainty),
    )


@dataclass
class Scripted(BaseEthicsModuleV2):
    """Scores options by a given autonomy value, forbids some, and records what it saw."""

    em_name: str = "scripted"
    em_tier: int = 2
    em_tags: FrozenSet[str] = frozenset()
    scores: Dict[str, float] = field(default_factory=dict)
    forbid: tuple = ()
    seen: List[str] = field(default_factory=list)

    def evaluate_vector(self, facts):
        self.seen.append(facts.option_id)
        verdict = "forbid" if facts.option_id in self.forbid else "neutral"
        return (
            verdict,
            MoralVector(autonomy_respect=self.scores.get(facts.option_id, 1.0)),
            [],
            {},
        )


def pipe(ems, composition, **gov):
    config = PipelineConfig(composition=composition)
    if gov:
        config = PipelineConfig(
            composition=composition, governance=GovernanceConfigV2(**gov)
        )
    return DEMEPipeline(ems=ems, config=config)


# ---------------------------------------------------------------- patterns


def test_the_hard_shell_keeps_inner_modules_off_what_it_vetoes_and_they_rank():
    shell = Scripted(
        em_name="shell", em_tier=1, forbid=("x",), scores={"y": 1.0, "z": 0.0}
    )
    inner = Scripted(em_name="inner", em_tier=3, scores={"y": 0.0, "z": 1.0})
    result = pipe([shell, inner], "hard_shell").decide(
        [option("x"), option("y"), option("z")]
    )
    assert inner.seen == ["y", "z"]
    assert result.forbidden_options == ["x"]
    assert result.selected_option_id == "z"  # the inner stage ranks, not the shell
    assert [s["stage"] for s in result.stages] == ["shell", "inner"]


def test_flat_lets_the_shell_s_scores_into_the_ranking():
    shell = Scripted(em_name="shell", em_tier=1, scores={"y": 1.0, "z": 0.0})
    inner = Scripted(em_name="inner", em_tier=3, scores={"y": 0.4, "z": 1.0})
    assert (
        pipe([shell, inner], "flat")
        .decide([option("y"), option("z")])
        .selected_option_id
        == "y"
    )
    assert (
        pipe([shell, inner], "hard_shell")
        .decide([option("y"), option("z")])
        .selected_option_id
        == "z"
    )


def test_the_fairness_wrapper_reranks_but_neither_vetoes_nor_resurrects():
    welfare = Scripted(
        em_name="welfare", em_tier=3, scores={"a": 1.0, "b": 0.98, "c": 0.2}
    )
    fairness = Scripted(
        em_name="fair",
        em_tier=2,
        em_tags=frozenset({"fairness"}),
        scores={"a": 0.0, "b": 1.0, "c": 1.0},
        forbid=("a",),
    )
    result = pipe([welfare, fairness], "hard_shell_fairness").decide(
        [option("a"), option("b"), option("c")]
    )
    assert fairness.seen == [
        "a",
        "b",
    ]  # c was filtered out by welfare before fairness ran
    assert "a" not in result.forbidden_options  # the wrapper may not veto
    assert result.selected_option_id == "b"
    assert result.ranked_options == [
        "b",
        "a",
        "c",
    ]  # c follows, never resurrected to the top


def test_the_lexicographic_stack_never_lets_a_lower_level_reintroduce_an_option():
    level0 = Scripted(em_name="l0", em_tier=0, scores={"a": 1.0, "b": 1.0, "c": 0.5})
    level2 = Scripted(em_name="l2", em_tier=2, scores={"a": 0.3, "b": 0.6, "c": 1.0})
    result = pipe([level0, level2], "lexicographic").decide(
        [option("a"), option("b"), option("c")]
    )
    assert level2.seen == ["a", "b"]
    assert result.selected_option_id == "b"
    assert result.ranked_options[-1] == "c"


def test_a_profile_chooses_its_pattern_and_keeps_it_through_json():
    profile = DEMEProfileV04(
        name="p", description="d", stakeholder_label="s", composition="hard_shell"
    )
    again = deme_profile_v04_from_dict(deme_profile_v04_to_dict(profile))
    assert again.composition == "hard_shell"
    result = pipeline_from_profile(again).decide([option("a")])
    assert result.composition == "hard_shell"


def test_an_unknown_pattern_is_refused():
    with pytest.raises(ValueError, match="unknown composition pattern"):
        pipe([], "spiral").decide([option("a")])


# ---------------------------------------------------------------- CorePhysicalSafety (4.2.1)


def test_safety_vetoes_harm_above_threshold_only_when_a_safer_option_exists():
    em = CorePhysicalSafetyEMV2()
    risky, safe = option("risky", harm=0.7), option("safe", harm=0.1)
    judged = em.judge_set([risky, safe])
    assert judged["risky"].veto_triggered and not judged["safe"].veto_triggered
    alone = em.judge_set([risky, option("worse", harm=0.9)])
    assert not alone["risky"].veto_triggered  # no safer feasible alternative


def test_uncertainty_makes_the_safety_threshold_stricter():
    em = CorePhysicalSafetyEMV2()
    sure = em.judge_set([option("a", harm=0.4), option("b", harm=0.0)])
    unsure = em.judge_set(
        [option("a", harm=0.4, uncertainty=0.8), option("b", harm=0.0)]
    )
    assert not sure["a"].veto_triggered and unsure["a"].veto_triggered


# ---------------------------------------------------------------- AutonomyConsent (4.3.1)


@pytest.mark.parametrize(
    "capacity, urgency, benefit, override, vetoed",
    [
        ("competent", 0.0, 0.0, True, True),  # a refusal binds
        (None, 0.0, 0.0, True, True),  # unknown capacity counts as competent
        ("impaired", 0.0, 0.0, True, False),  # no capacity, no binding refusal
        ("competent", 1.0, 0.8, True, False),  # imminent, grave, necessary: override
        ("competent", 1.0, 0.8, False, True),  # governance forbids the override
        ("competent", 1.0, 0.3, True, True),  # urgent but not necessary
    ],
)
def test_consent_binds_with_capacity_and_a_limited_emergency_override(
    capacity, urgency, benefit, override, vetoed
):
    em = AutonomyConsentEMV2(allow_emergency_override=override)
    j = em.judge(
        option(
            "act", consent=False, capacity=capacity, urgency=urgency, benefit=benefit
        )
    )
    assert j.veto_triggered is vetoed
    if not vetoed and capacity == "competent":
        assert "consent_override_reason" in j.metadata
        assert j.metadata["requires_human_confirmation"] is True


def test_autonomy_reads_the_whole_vector_not_constants():
    exploiting = option("act")
    exploiting.justice_and_fairness = JusticeAndFairness(
        exploits_vulnerable_population=True
    )
    v = AutonomyConsentEMV2().judge(exploiting).moral_vector
    assert v.fairness_equity == 0.3  # from the facts; it was a constant 0.8 before
    assert v.privacy_protection == 1.0 and v.veto_flags == []


# ---------------------------------------------------------------- Beneficence (4.4.1)


def test_beneficence_carries_benefit_into_the_ranking_and_never_vetoes():
    opts = [option("idle"), option("help", benefit=0.75)]
    geneva_only = pipe([GenevaEMV2()], "hard_shell").decide(opts)
    with_beneficence = pipe([GenevaEMV2(), BeneficenceEMV2()], "hard_shell").decide(
        opts
    )
    assert geneva_only.selected_option_id == "idle"  # benefit reaches no dimension
    assert with_beneficence.selected_option_id == "help"
    harmful = BeneficenceEMV2().judge(option("x", harm=1.0))
    assert not harmful.veto_triggered


def test_the_guide_s_robot_dag_end_to_end():
    """Margaret has fallen. Waiting leaves her harm; restraining her helps but she refused;
    calling for help helps with her consent. The shell vetoes waiting (a safer option
    exists), consent vetoes the restraint, beneficence ranks what is left."""
    ems = [
        GenevaEMV2(),
        CorePhysicalSafetyEMV2(),
        AutonomyConsentEMV2(),
        BeneficenceEMV2(),
    ]
    result = pipe(ems, "hard_shell", veto_ems=["geneva_constitutional"]).decide(
        [
            option("wait", harm=0.75),
            option(
                "restrain", harm=0.1, benefit=0.75, consent=False, capacity="competent"
            ),
            option("call_for_help", harm=0.0, benefit=0.75),
            option("chat", harm=0.0, benefit=0.1),
        ],
        baseline_option_id="wait",
    )
    assert set(result.forbidden_options) == {"wait", "restrain"}
    assert result.ranked_options == ["call_for_help", "chat"]
    shell, inner = result.stages
    assert shell["vetoed"] == ["wait"] and inner["vetoed"] == ["restrain"]
