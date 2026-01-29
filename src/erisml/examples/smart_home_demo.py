"""
Smart Home Ethics Demo - The "Fireman's Dilemma"

This script demonstrates ErisML's "Leash" capability in a Smart Home context.
Scenario:
    A Fireman is trying to enter the home to put out a fire. The homeowner is away.
    The Smart Lock AI must decide:
    1. BLOCK ENTRY: Follows the strict rule "No strangers allowed" (Protects Privacy).
    2. ALLOW ENTRY: Breaks the rule, but prevents catastrophic usage (Protects Life).

This demo visualizes the "Moral Vector" - the mathematical reasoning behind the decision.
"""

from __future__ import annotations


import sys
import os
import codecs

# Ensure we use the local 'src' directory, avoiding installed package mismatches
current_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate up from src/erisml/examples -> src
# src/erisml/examples -> src/erisml -> src
src_path = os.path.abspath(os.path.join(current_dir, "../.."))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Reconfigure stdout to handle UTF-8 for emoji support on Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())


from erisml.ethics import (  # noqa: E402
    AutonomyAndAgency,
    Consequences,
    EpistemicStatus,
    EthicalFacts,
    JusticeAndFairness,
    RightsAndDuties,
    PrivacyAndDataGovernance,  # Added for this scenario
)

# We'll use the basic Module interface to create a custom "HomeGuardian"
from erisml.ethics.modules.base import EthicsModule  # noqa: E402
from erisml.ethics.judgement import EthicalJudgement  # noqa: E402


# --- Helper: ASCII Chart Visualizer ---
def draw_moral_compass(facts: EthicalFacts, label: str):
    """Draws a simple bar chart of key ethical dimensions."""
    print(f"\n[ Moral Compass: {label} ]")

    # Extract key normalized scores (0.0 to 1.0)
    # Note: These mappings depend on how ErisML calculates 'scores' from raw facts.
    # For this demo, we'll approximate based on the input facts for visualization.

    # Harm Risk (Inverted: 1.0 is SAFE, 0.0 is DANGER)
    safety_score = 1.0 - facts.consequences.expected_harm

    # Rights/Privacy (1.0 is RESPECTED, 0.0 is VIOLATED)
    # We combine privacy and rights for a simple view
    privacy_score = 1.0 if not facts.rights_and_duties.violates_rights else 0.2

    benefit_score = facts.consequences.expected_benefit

    dimensions = [
        ("Safety ", safety_score, "🔴" if safety_score < 0.5 else "Tm"),
        ("Privacy", privacy_score, "🔒"),
        ("Benefit", benefit_score, "mj"),
    ]

    for name, score, icon in dimensions:
        bar_len = int(score * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"  {name} |{bar}| {score:.2f} {icon}")


# --- Step 1: Define the Scenario Options ---


def create_block_entry_option() -> EthicalFacts:
    """Option A: Keep door locked."""
    return EthicalFacts(
        option_id="BLOCK_ENTRY",
        # High Harm: House burns down (Harm=0.9)
        consequences=Consequences(
            expected_benefit=0.0,
            expected_harm=0.9,  # CATASTROPHIC
            urgency=0.9,
            affected_count=1,  # The Homeowner
        ),
        # Rights: Perfect respect for privacy rules
        rights_and_duties=RightsAndDuties(
            violates_rights=False,
            has_valid_consent=False,  # No consent to enter needed if blocked
            violates_explicit_rule=False,
            role_duty_conflict=False,
        ),
        # Privacy: Protected (Option A)
        privacy_and_data=PrivacyAndDataGovernance(
            privacy_invasion_level=0.0,
            data_minimization_respected=True,
            secondary_use_without_consent=False,
            data_retention_excessive=False,
            reidentification_risk=0.0,
        ),
        justice_and_fairness=JusticeAndFairness(discriminates_on_protected_attr=False),
        autonomy_and_agency=AutonomyAndAgency(has_meaningful_choice=True),
        epistemic_status=EpistemicStatus(
            uncertainty_level=0.1, evidence_quality="high"
        ),
    )


def create_allow_entry_option() -> EthicalFacts:
    """Option B: Unlock door for Fireman."""
    return EthicalFacts(
        option_id="ALLOW_ENTRY",
        # Low Harm: Fire put out (Harm=0.1 risk of property damage during entry)
        consequences=Consequences(
            expected_benefit=0.9,  # CA House and neighborhood saved
            expected_harm=0.1,  # Minor door damage
            urgency=0.9,
            affected_count=5,  # Neighbors saved too
        ),
        # Rights: Violates the "No Strangers" rule
        rights_and_duties=RightsAndDuties(
            violates_rights=True,  # Technical violation of property right
            has_valid_consent=False,  # We don't have explicit owner consent
            violates_explicit_rule=True,  # Violates "Always Lock" setting
            role_duty_conflict=True,  # Conflict: Duty to protect vs Duty to obey settings
        ),
        # Privacy: Impacted (Option B)
        privacy_and_data=PrivacyAndDataGovernance(
            privacy_invasion_level=0.8,
            data_minimization_respected=True,
            secondary_use_without_consent=True,  # Stranger enters without consent
            data_retention_excessive=False,
            reidentification_risk=0.0,
        ),
        justice_and_fairness=JusticeAndFairness(discriminates_on_protected_attr=False),
        autonomy_and_agency=AutonomyAndAgency(has_meaningful_choice=True),
        epistemic_status=EpistemicStatus(
            uncertainty_level=0.1, evidence_quality="high"
        ),
    )


def create_uncertain_entry_option() -> EthicalFacts:
    """Option C: The Thief (Deception Scenario).
    Looks like a fireman, but evidence is low quality (blurry cam, no thermal heat).
    """
    return EthicalFacts(
        option_id="UNCERTAIN_ENTRY",
        # Potential High Benefit (IF it's a real fire), but we assume high stakes
        consequences=Consequences(
            expected_benefit=0.9,
            expected_harm=0.1,
            urgency=0.9,
            affected_count=5,
        ),
        rights_and_duties=RightsAndDuties(
            violates_rights=True,
            has_valid_consent=False,
            violates_explicit_rule=True,
            role_duty_conflict=True,
        ),
        privacy_and_data=PrivacyAndDataGovernance(
            privacy_invasion_level=0.8,
            data_minimization_respected=True,
            secondary_use_without_consent=True,
            data_retention_excessive=False,
            reidentification_risk=0.0,
        ),
        justice_and_fairness=JusticeAndFairness(discriminates_on_protected_attr=False),
        autonomy_and_agency=AutonomyAndAgency(has_meaningful_choice=True),
        # CRITICAL: High Uncertainty! The system suspects deception.
        epistemic_status=EpistemicStatus(uncertainty_level=0.8, evidence_quality="low"),
    )


def create_false_alarm_option() -> EthicalFacts:
    """Option D: Burnt Toast (False Alarm).
    Fire alarm active, but thermal sensors show minimal heat.
    """
    return EthicalFacts(
        option_id="FALSE_ALARM_ENTRY",
        # Low Benefit: "Saving" the house from burnt toast isn't worth a break-in
        consequences=Consequences(
            expected_benefit=0.1,  # Saving toast
            expected_harm=0.0,
            urgency=0.2,  # Low urgency
            affected_count=1,
        ),
        rights_and_duties=RightsAndDuties(
            violates_rights=True,  # Still a break-in
            has_valid_consent=False,
            violates_explicit_rule=True,
            role_duty_conflict=False,
        ),
        privacy_and_data=PrivacyAndDataGovernance(
            privacy_invasion_level=0.8,
            data_minimization_respected=True,
            secondary_use_without_consent=True,
            data_retention_excessive=False,
            reidentification_risk=0.0,
        ),
        justice_and_fairness=JusticeAndFairness(discriminates_on_protected_attr=False),
        autonomy_and_agency=AutonomyAndAgency(has_meaningful_choice=True),
        epistemic_status=EpistemicStatus(
            uncertainty_level=0.1, evidence_quality="high"
        ),
    )


# --- Step 2: The "Leash" (Ethics Module) ---


class EmergencyGuardianEM(EthicsModule):
    """
    A custom Ethics Module for Smart Homes.
    Prioritizes LIFE_SAFETY (Consequences) over PROPERTY_RIGHTS (Privacy).
    Handes UNCERTAINTY (Thief Detection).
    """

    def __init__(self):
        # Initialize attributes directly since EthicsModule is an abstract interface
        self.em_name = "EmergencyGuardian"
        self.stakeholder = "Homeowner"
        # calls object.__init__
        super().__init__()

    def judge(self, facts: EthicalFacts) -> EthicalJudgement:
        # Calculate "Effective Benefit" by discounting for uncertainty
        # If we are 80% uncertain, the benefit is heavily penalized.
        uncertainty = (
            facts.epistemic_status.uncertainty_level if facts.epistemic_status else 0.0
        )
        benefit = facts.consequences.expected_benefit if facts.consequences else 0.0
        harm = facts.consequences.expected_harm if facts.consequences else 0.0

        effective_benefit = benefit * (1.0 - uncertainty)

        # 1. CORE SAFETY CHECK (The "Leash" tightens)
        # If harm is catastrophic (>0.8), we MUST avoid this option.
        if harm > 0.8:
            return EthicalJudgement(
                option_id=facts.option_id,
                em_name=self.em_name,
                stakeholder=self.stakeholder,
                verdict="forbid",
                normative_score=0.0,
                reasons=["Blocked: Catastrophic harm risk detected."],
                metadata={},
            )

        # 2. EMERGENCY OVERRIDE (With Uncertainty Check)
        # If effective benefit is high, we override privacy.
        # But if uncertainty is high (The Thief), effective_benefit will be low.
        if effective_benefit > 0.6 and facts.rights_and_duties.violates_rights:
            return EthicalJudgement(
                option_id=facts.option_id,
                em_name=self.em_name,
                stakeholder=self.stakeholder,
                verdict="prefer",
                normative_score=effective_benefit,
                reasons=[
                    "Approved: Emergency override. Promoting welfare outweighs privacy violation."
                ],
                metadata={},
            )

        # 3. HIGH UNCERTAINTY / THIEF CHECK
        if uncertainty > 0.5 and facts.rights_and_duties.violates_rights:
            return EthicalJudgement(
                option_id=facts.option_id,
                em_name=self.em_name,
                stakeholder=self.stakeholder,
                verdict="forbid",
                normative_score=0.1,
                reasons=[
                    f"Blocked: Suspicious activity (Uncertainty: {uncertainty:.1f}). Security Protocols Active."
                ],
                metadata={},
            )

        # 4. FALSE ALARM CHECK
        if benefit < 0.3 and facts.rights_and_duties.violates_rights:
            return EthicalJudgement(
                option_id=facts.option_id,
                em_name=self.em_name,
                stakeholder=self.stakeholder,
                verdict="avoid",
                normative_score=0.3,
                reasons=[
                    "Avoid: Benefit (e.g. burnt toast) too low to justify privacy violation."
                ],
                metadata={},
            )

        # Default logic for normal cases
        if facts.rights_and_duties.violates_rights:
            return EthicalJudgement(
                option_id=facts.option_id,
                em_name=self.em_name,
                stakeholder=self.stakeholder,
                verdict="forbid",
                normative_score=0.1,
                reasons=["Blocked: Rights violation."],
                metadata={},
            )

        return EthicalJudgement(
            option_id=facts.option_id,
            em_name=self.em_name,
            stakeholder=self.stakeholder,
            verdict="prefer",
            normative_score=0.6,
            reasons=["Standard permitted action."],
            metadata={},
        )


def main():
    print("\n🏠 --- SMART HOME AI: EDGE CASE ANALYSIS --- 🏠")

    # 1. Generate Options
    opt_real = create_allow_entry_option()  # The Real Fireman
    opt_thief = create_uncertain_entry_option()  # The Fake Fireman
    opt_toast = create_false_alarm_option()  # The Burnt Toast

    # 3. Apply The Leash
    print("\n🤖 [ SYSTEM PROCESSING: ErisML Governance Layer ]")
    guardian = EmergencyGuardianEM()

    judgement_real = guardian.judge(opt_real)
    judgement_thief = guardian.judge(opt_thief)
    judgement_toast = guardian.judge(opt_toast)

    # 4. Show Results
    print("\n📋 DECISION MATRIX:")
    print("-" * 80)
    print(
        f"Scenario 1 (Real Fire):   {judgement_real.verdict.upper():<10} [{judgement_real.reasons[0]}]"
    )
    print(
        f"Scenario 2 (The Thief):   {judgement_thief.verdict.upper():<10} [{judgement_thief.reasons[0]}]"
    )
    print(
        f"Scenario 3 (Burnt Toast): {judgement_toast.verdict.upper():<10} [{judgement_toast.reasons[0]}]"
    )
    print("-" * 80)

    print("\n🎉 SUMMARY:")
    print("1. Real Emergency:  Allowed. (Safety > Privacy)")
    print(
        "2. The Thief:       BLOCKED. (Uncertainty penalty applied. 'Better safe than sorry')"
    )
    print("3. Burnt Toast:     AVOIDED. (Benefit too low to break the door)")


if __name__ == "__main__":
    main()
