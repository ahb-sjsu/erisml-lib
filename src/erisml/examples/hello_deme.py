"""
Hello DEME - A Simple Introduction to ErisML's Ethics Module System

This example demonstrates the basic workflow of DEME (Democratically Governed
Ethics Modules):

1. Create EthicalFacts for candidate options
2. Evaluate options using an Ethics Module
3. View the ethical judgements

This is the simplest possible example - just two options and one ethics module.
For more complex examples, see:
  - triage_ethics_demo.py (clinical triage with multiple EMs and governance)
  - greek_tragedy_pantheon_demo.py (complex scenarios with tragic conflicts)
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


def make_simple_option(option_id: str, violates_rights: bool, expected_benefit: float) -> EthicalFacts:
    """
    Create a simple EthicalFacts object with minimal required fields.
    
    Args:
        option_id: Unique identifier for this option
        violates_rights: Whether this option violates individual rights
        expected_benefit: Expected benefit score (0.0 to 1.0)
    
    Returns:
        EthicalFacts instance with required fields populated
    """
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
        # Optional fields - we'll include a few to show how they work
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
    """
    Main function demonstrating basic DEME usage.
    """
    print("=" * 70)
    print("Hello DEME - Simple Ethics Module Demo")
    print("=" * 70)
    print()
    
    # Step 1: Create candidate options as EthicalFacts
    print("Step 1: Creating two candidate options...")
    print()
    
    # Option A: Respects rights, high benefit
    option_a = make_simple_option(
        option_id="option_a",
        violates_rights=False,
        expected_benefit=0.8,
    )
    print(f"  Option A: Respects rights, high benefit (0.8)")
    
    # Option B: Violates rights, high benefit
    option_b = make_simple_option(
        option_id="option_b",
        violates_rights=True,
        expected_benefit=0.8,
    )
    print(f"  Option B: Violates rights, high benefit (0.8)")
    print()
    
    # Step 2: Instantiate an Ethics Module
    print("Step 2: Instantiating RightsFirstEM (rights-first ethics module)...")
    print()
    em = RightsFirstEM()
    print(f"  Ethics Module: {em.em_name}")
    print(f"  Stakeholder: {em.stakeholder}")
    print()
    
    # Step 3: Evaluate each option
    print("Step 3: Evaluating options with the ethics module...")
    print()
    
    judgement_a = em.judge(option_a)
    judgement_b = em.judge(option_b)
    
    # Step 4: Display results
    print("Step 4: Results")
    print()
    print("-" * 70)
    print(f"Option A: {option_a.option_id}")
    print(f"  Verdict: {judgement_a.verdict}")
    print(f"  Normative Score: {judgement_a.normative_score:.3f}")
    print(f"  Reasons:")
    for reason in judgement_a.reasons:
        print(f"    - {reason}")
    print()
    
    print("-" * 70)
    print(f"Option B: {option_b.option_id}")
    print(f"  Verdict: {judgement_b.verdict}")
    print(f"  Normative Score: {judgement_b.normative_score:.3f}")
    print(f"  Reasons:")
    for reason in judgement_b.reasons:
        print(f"    - {reason}")
    print()
    
    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print()
    print("Key Takeaway:")
    print("  Option A (respects rights) →", judgement_a.verdict, f"(score: {judgement_a.normative_score:.3f})")
    print("  Option B (violates rights) →", judgement_b.verdict, f"(score: {judgement_b.normative_score:.3f})")
    print()
    print("RightsFirstEM prioritizes rights protection - even if both options")
    print("have the same expected benefit, Option B is forbidden because it")
    print("violates rights.")
    print()
    print("Next Steps:")
    print("  - See triage_ethics_demo.py for multi-option governance")
    print("  - See greek_tragedy_pantheon_demo.py for complex scenarios")
    print("  - Write your own EthicsModule by implementing the EthicsModule protocol")
    print()


if __name__ == "__main__":
    main()

