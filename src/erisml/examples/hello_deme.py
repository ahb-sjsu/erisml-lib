"""
Hello DEME - A Simple Introduction to ErisML's Ethics Module System
"""

from __future__ import annotations

from erisml.ethics import (
    AutonomyAndAgency,
    Consequences,
    EpistemicStatus,
    EthicalFacts,
    JusticeAndFairness,
    RightsAndDuties,
)
from erisml.ethics.modules.triage_em import RightsFirstEM


def make_simple_option(
    option_id: str, violates_rights: bool, expected_benefit: float
) -> EthicalFacts:
    return EthicalFacts(
        option_id=option_id,
        consequences=Consequences(
            expected_benefit=expected_benefit,
            expected_harm=0.2,
            urgency=0.5,
            affected_count=1,
        ),
        rights_and_duties=RightsAndDuties(
            violates_rights=violates_rights,
            has_valid_consent=True,
            violates_explicit_rule=False,
            role_duty_conflict=False,
        ),
        justice_and_fairness=JusticeAndFairness(
            discriminates_on_protected_attr=False,
            prioritizes_most_disadvantaged=False,
            exploits_vulnerable_population=False,
            exacerbates_power_imbalance=False,
        ),
        autonomy_and_agency=AutonomyAndAgency(
            has_meaningful_choice=True,
            coercion_or_undue_influence=not violates_rights,
            can_withdraw_without_penalty=True,
            manipulative_design_present=False,
        ),
        epistemic_status=EpistemicStatus(
            uncertainty_level=0.2,
            evidence_quality="high",
            novel_situation_flag=False,
        ),
    )


def main() -> None:
    print("=" * 70)
    print("Hello DEME - Simple Ethics Module Demo")
    print("=" * 70)
    print()

    # Step 1: Create candidate options
    print("Step 1: Creating two candidate options...")
    print()

    option_a = make_simple_option("option_a", False, 0.8)
    print("  Option A: Respects rights, high benefit (0.8)")

    option_b = make_simple_option("option_b", True, 0.8)
    print("  Option B: Violates rights, high benefit (0.8)")
    print()

    # Step 2: Instantiate Module
    print("Step 2: Instantiating RightsFirstEM...")
    print()
    em = RightsFirstEM()
    print(f"  Ethics Module: {em.em_name}")
    print(f"  Stakeholder: {em.stakeholder}")
    print()

    # Step 3: Evaluate
    print("Step 3: Evaluating options...")
    print()

    judgement_a = em.judge(option_a)
    judgement_b = em.judge(option_b)

    # Step 4: Results
    print("Step 4: Results")
    print()
    print("-" * 70)
    print(f"Option A: {option_a.option_id}")
    print(f"  Verdict: {judgement_a.verdict}")
    print(f"  Normative Score: {judgement_a.normative_score:.3f}")
    print()

    print("-" * 70)
    print(f"Option B: {option_b.option_id}")
    print(f"  Verdict: {judgement_b.verdict}")
    print(f"  Normative Score: {judgement_b.normative_score:.3f}")
    print()


if __name__ == "__main__":
    main()
