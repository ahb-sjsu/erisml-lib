# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
DEME 2.0 Demo: MoralVector-based Ethical Reasoning

This demo showcases the DEME 2.0 features:
1. MoralVector: k-dimensional ethical assessment (8+1 dimensions)
2. EthicalJudgementV2: EM outputs with moral vectors and explicit vetoes
3. GovernanceConfigV2: Tier-based weighting and lexical priorities
4. select_option_v2: V2 decision aggregation with Pareto-aware ranking
5. MoralLandscape: Pareto frontier analysis for multi-option comparison

Usage:
    python -m erisml.examples.deme_2_demo

Key Differences from V1:
- Scalar normative_score replaced by 8+1 dimensional MoralVector
- Explicit veto flags with tier-based veto authority
- Dimension weights configurable for domain-specific ethics
- Pareto dominance analysis for multi-objective reasoning
"""

from __future__ import annotations

from typing import Dict, List

from erisml.ethics import (
    # V1 facts (still used as input)
    EthicalFacts,
    Consequences,
    RightsAndDuties,
    JusticeAndFairness,
    AutonomyAndAgency,
    PrivacyAndDataGovernance,
    ProceduralAndLegitimacy,
    EpistemicStatus,
    # V2 types
    MoralVector,
    MoralLandscape,
    EthicalJudgementV2,
    # V2 governance
    GovernanceConfigV2,
    DimensionWeights,
    DecisionOutcomeV2,
    select_option_v2,
)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def print_section(title: str) -> None:
    """Print a section header."""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_moral_vector(mv: MoralVector, indent: str = "  ") -> None:
    """Pretty-print a MoralVector's dimensions."""
    dims = [
        ("physical_harm", mv.physical_harm, "lower is better"),
        ("rights_respect", mv.rights_respect, "higher is better"),
        ("fairness_equity", mv.fairness_equity, "higher is better"),
        ("autonomy_respect", mv.autonomy_respect, "higher is better"),
        ("privacy_protection", mv.privacy_protection, "higher is better"),
        ("societal_environmental", mv.societal_environmental, "higher is better"),
        ("virtue_care", mv.virtue_care, "higher is better"),
        ("legitimacy_trust", mv.legitimacy_trust, "higher is better"),
        ("epistemic_quality", mv.epistemic_quality, "higher is better"),
    ]

    for name, value, note in dims:
        bar = "#" * int(value * 20)
        print(f"{indent}{name:25s} [{bar:20s}] {value:.2f}  ({note})")

    if mv.veto_flags:
        print(f"{indent}VETO FLAGS: {mv.veto_flags}")
    if mv.reason_codes:
        print(f"{indent}Reasons: {mv.reason_codes[:3]}")


# =============================================================================
# DEMO: MORAL VECTOR BASICS
# =============================================================================


def demo_moral_vector_basics() -> None:
    """Demonstrate MoralVector creation and operations."""
    print_section("MoralVector Basics")

    print(
        """
MoralVector replaces scalar normative_score with 8+1 dimensions:
- 8 ethical dimensions from EthicalFacts (harm, rights, fairness, etc.)
- +1 epistemic dimension (uncertainty, evidence quality)
"""
    )

    # Create from scratch
    print("1. Creating MoralVectors manually:")

    good_option = MoralVector(
        physical_harm=0.1,  # Low harm
        rights_respect=0.9,  # High rights respect
        fairness_equity=0.85,  # Fair
        autonomy_respect=0.9,  # High autonomy
        privacy_protection=0.8,  # Good privacy
        societal_environmental=0.7,
        virtue_care=0.8,
        legitimacy_trust=0.9,
        epistemic_quality=0.85,
    )

    problematic_option = MoralVector(
        physical_harm=0.3,
        rights_respect=0.0,  # Rights violation!
        fairness_equity=0.2,  # Discriminatory
        autonomy_respect=0.3,
        privacy_protection=0.4,
        societal_environmental=0.5,
        virtue_care=0.4,
        legitimacy_trust=0.3,
        epistemic_quality=0.6,
        veto_flags=["RIGHTS_VIOLATION", "DISCRIMINATION"],
    )

    print("\n  Good Option:")
    print_moral_vector(good_option)
    print(f"    Scalar score: {good_option.to_scalar():.3f}")

    print("\n  Problematic Option:")
    print_moral_vector(problematic_option)
    print(f"    Scalar score: {problematic_option.to_scalar():.3f}")
    print(f"    Has veto: {problematic_option.has_veto()}")

    # Pareto dominance
    print("\n2. Pareto Dominance Check:")
    print(f"  Good dominates Problematic: {good_option.dominates(problematic_option)}")
    print(f"  Problematic dominates Good: {problematic_option.dominates(good_option)}")

    # Distance metrics
    print("\n3. Distance Metrics:")
    print(
        f"  Euclidean distance: {good_option.distance(problematic_option, 'euclidean'):.3f}"
    )
    print(
        f"  Manhattan distance: {good_option.distance(problematic_option, 'manhattan'):.3f}"
    )


# =============================================================================
# DEMO: EXTRACTING MORAL VECTOR FROM ETHICAL FACTS
# =============================================================================


def demo_from_ethical_facts() -> None:
    """Demonstrate MoralVector extraction from EthicalFacts."""
    print_section("MoralVector from EthicalFacts")

    print(
        """
MoralVector.from_ethical_facts() provides a standard mapping from
structured EthicalFacts to the 8+1 moral dimensions.
"""
    )

    facts = EthicalFacts(
        option_id="emergency_treatment",
        consequences=Consequences(
            expected_benefit=0.9,
            expected_harm=0.15,
            urgency=0.95,
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
        privacy_and_data=PrivacyAndDataGovernance(
            privacy_invasion_level=0.2,
            data_minimization_respected=True,
            secondary_use_without_consent=False,
            data_retention_excessive=False,
            reidentification_risk=0.1,
        ),
        procedural_and_legitimacy=ProceduralAndLegitimacy(
            followed_approved_procedure=True,
            stakeholders_consulted=True,
            decision_explainable_to_public=True,
            contestation_available=True,
        ),
        epistemic_status=EpistemicStatus(
            uncertainty_level=0.2,
            evidence_quality="high",
            novel_situation_flag=False,
        ),
    )

    mv = MoralVector.from_ethical_facts(facts)

    print(f"EthicalFacts: {facts.option_id}")
    print("\nExtracted MoralVector:")
    print_moral_vector(mv)
    print(f"\nScalar score: {mv.to_scalar():.3f}")


# =============================================================================
# DEMO: ETHICAL JUDGEMENT V2
# =============================================================================


def demo_ethical_judgement_v2() -> None:
    """Demonstrate EthicalJudgementV2 with moral vectors."""
    print_section("EthicalJudgementV2")

    print(
        """
EthicalJudgementV2 replaces normative_score with MoralVector and adds:
- em_tier: Classification for weighted aggregation (0-4)
- veto_triggered: Explicit veto flag
- confidence: EM's confidence in its assessment
"""
    )

    # Tier 0 (Constitutional) judgement
    geneva_judgement = EthicalJudgementV2(
        option_id="treatment_A",
        em_name="geneva_em",
        stakeholder="patients_and_public",
        em_tier=0,  # Constitutional tier
        verdict="prefer",
        moral_vector=MoralVector(
            physical_harm=0.1,
            rights_respect=1.0,
            fairness_equity=0.9,
            autonomy_respect=0.95,
            privacy_protection=0.85,
            societal_environmental=0.8,
            virtue_care=0.9,
            legitimacy_trust=0.95,
            epistemic_quality=0.9,
        ),
        veto_triggered=False,
        confidence=0.95,
        reasons=["No rights violations", "Proper consent obtained"],
    )

    # Tier 2 (Rights/Fairness) judgement
    fairness_judgement = EthicalJudgementV2(
        option_id="treatment_A",
        em_name="allocation_fairness_em",
        stakeholder="patients_and_public",
        em_tier=2,  # Rights/Fairness tier
        verdict="strongly_prefer",
        moral_vector=MoralVector(
            physical_harm=0.15,
            rights_respect=0.9,
            fairness_equity=0.95,
            autonomy_respect=0.85,
            privacy_protection=0.8,
            societal_environmental=0.75,
            virtue_care=0.85,
            legitimacy_trust=0.9,
            epistemic_quality=0.85,
        ),
        veto_triggered=False,
        confidence=0.9,
        reasons=["Prioritizes most disadvantaged", "Fair allocation"],
    )

    print("Geneva EM (Tier 0 - Constitutional):")
    print(f"  Verdict: {geneva_judgement.verdict}")
    print(f"  EM Tier: {geneva_judgement.em_tier}")
    print(f"  Confidence: {geneva_judgement.confidence}")
    print(f"  Scalar (for V1 compat): {geneva_judgement.normative_score:.3f}")

    print("\nFairness EM (Tier 2 - Rights/Fairness):")
    print(f"  Verdict: {fairness_judgement.verdict}")
    print(f"  EM Tier: {fairness_judgement.em_tier}")
    print(f"  Confidence: {fairness_judgement.confidence}")
    print(f"  Scalar (for V1 compat): {fairness_judgement.normative_score:.3f}")


# =============================================================================
# DEMO: GOVERNANCE V2
# =============================================================================


def demo_governance_v2() -> None:
    """Demonstrate GovernanceConfigV2 and select_option_v2."""
    print_section("Governance V2: Tier-Based Aggregation")

    print(
        """
GovernanceConfigV2 provides:
- DimensionWeights: Per-dimension weights for scalar collapse
- Tier-based weighting: Constitutional EMs weighted 10x, Core Safety 5x, etc.
- Lexical priorities: DAG-based conflict resolution
"""
    )

    # Configure governance
    config = GovernanceConfigV2(
        dimension_weights=DimensionWeights(
            physical_harm=1.5,  # Higher weight on harm prevention
            rights_respect=1.2,  # Rights are important
            fairness_equity=1.0,
            autonomy_respect=1.0,
            privacy_protection=0.9,
            societal_environmental=0.7,
            virtue_care=0.6,
            legitimacy_trust=1.0,
            epistemic_quality=0.4,
        ),
        # Default tier configs: tier 0 = 10x, tier 1 = 5x, tier 2 = 2x, etc.
        require_non_forbidden=True,
        tie_breaker="status_quo",
    )

    print("Dimension Weights:")
    for dim, weight in config.dimension_weights.to_dict().items():
        print(f"  {dim}: {weight}")

    print("\nTier Weights:")
    for tier in range(5):
        tc = config.get_tier_config(tier)
        print(
            f"  Tier {tier}: weight={tc.weight_multiplier}x, can_veto={tc.veto_enabled}"
        )

    # Create judgements for 3 options
    judgements_by_option: Dict[str, List[EthicalJudgementV2]] = {
        "option_A": [
            EthicalJudgementV2(
                option_id="option_A",
                em_name="geneva_em",
                stakeholder="public",
                em_tier=0,
                verdict="prefer",
                moral_vector=MoralVector(
                    physical_harm=0.1,
                    rights_respect=0.95,
                    fairness_equity=0.9,
                    autonomy_respect=0.9,
                    privacy_protection=0.85,
                    societal_environmental=0.8,
                    virtue_care=0.85,
                    legitimacy_trust=0.9,
                    epistemic_quality=0.9,
                ),
                reasons=["Good rights posture"],
            ),
            EthicalJudgementV2(
                option_id="option_A",
                em_name="fairness_em",
                stakeholder="public",
                em_tier=2,
                verdict="strongly_prefer",
                moral_vector=MoralVector(
                    physical_harm=0.15,
                    rights_respect=0.9,
                    fairness_equity=0.95,
                    autonomy_respect=0.85,
                    privacy_protection=0.8,
                    societal_environmental=0.75,
                    virtue_care=0.8,
                    legitimacy_trust=0.85,
                    epistemic_quality=0.85,
                ),
                reasons=["Maximally fair"],
            ),
        ],
        "option_B": [
            EthicalJudgementV2(
                option_id="option_B",
                em_name="geneva_em",
                stakeholder="public",
                em_tier=0,
                verdict="neutral",
                moral_vector=MoralVector(
                    physical_harm=0.3,
                    rights_respect=0.7,
                    fairness_equity=0.6,
                    autonomy_respect=0.7,
                    privacy_protection=0.6,
                    societal_environmental=0.5,
                    virtue_care=0.6,
                    legitimacy_trust=0.7,
                    epistemic_quality=0.7,
                ),
                reasons=["Acceptable but not ideal"],
            ),
            EthicalJudgementV2(
                option_id="option_B",
                em_name="fairness_em",
                stakeholder="public",
                em_tier=2,
                verdict="avoid",
                moral_vector=MoralVector(
                    physical_harm=0.35,
                    rights_respect=0.65,
                    fairness_equity=0.5,
                    autonomy_respect=0.6,
                    privacy_protection=0.55,
                    societal_environmental=0.45,
                    virtue_care=0.55,
                    legitimacy_trust=0.6,
                    epistemic_quality=0.65,
                ),
                reasons=["Some fairness concerns"],
            ),
        ],
        "option_C": [
            EthicalJudgementV2(
                option_id="option_C",
                em_name="geneva_em",
                stakeholder="public",
                em_tier=0,
                verdict="forbid",
                moral_vector=MoralVector(
                    physical_harm=0.6,
                    rights_respect=0.0,
                    fairness_equity=0.2,
                    autonomy_respect=0.2,
                    privacy_protection=0.3,
                    societal_environmental=0.3,
                    virtue_care=0.2,
                    legitimacy_trust=0.2,
                    epistemic_quality=0.5,
                    veto_flags=["RIGHTS_VIOLATION"],
                ),
                veto_triggered=True,
                veto_reason="Fundamental rights violation",
                reasons=["Rights violation detected"],
            ),
        ],
    }

    print("\n--- Running select_option_v2 ---")
    outcome: DecisionOutcomeV2 = select_option_v2(judgements_by_option, config)

    print(f"\nSelected: {outcome.selected_option_id}")
    print(f"Ranked: {outcome.ranked_options}")
    print(f"Forbidden: {outcome.forbidden_options}")
    print(f"Rationale: {outcome.rationale}")

    if outcome.veto_reasons:
        print("\nVeto Details:")
        for opt, reasons in outcome.veto_reasons.items():
            print(f"  {opt}: {reasons}")

    print("\nAggregated Scores:")
    for opt_id in ["option_A", "option_B", "option_C"]:
        if opt_id in outcome.aggregated_vectors:
            vec = outcome.aggregated_vectors[opt_id]
            score = vec.to_scalar(weights=config.dimension_weights.to_dict())
            print(f"  {opt_id}: {score:.3f}")


# =============================================================================
# DEMO: MORAL LANDSCAPE
# =============================================================================


def demo_moral_landscape() -> None:
    """Demonstrate MoralLandscape for Pareto analysis."""
    print_section("MoralLandscape: Pareto Frontier Analysis")

    print(
        """
MoralLandscape provides Pareto-optimal reasoning:
- pareto_frontier(): Find non-dominated options
- dominated_options(): Find options dominated by others
- Enables multi-objective decision making without forced scalar collapse
"""
    )

    # Create a landscape with multiple options
    options = {
        "fast_risky": MoralVector(
            physical_harm=0.4,
            rights_respect=0.8,
            fairness_equity=0.7,
            autonomy_respect=0.9,
            privacy_protection=0.6,
            societal_environmental=0.5,
            virtue_care=0.6,
            legitimacy_trust=0.7,
            epistemic_quality=0.8,
        ),
        "slow_safe": MoralVector(
            physical_harm=0.1,
            rights_respect=0.85,
            fairness_equity=0.8,
            autonomy_respect=0.7,
            privacy_protection=0.8,
            societal_environmental=0.7,
            virtue_care=0.8,
            legitimacy_trust=0.85,
            epistemic_quality=0.7,
        ),
        "balanced": MoralVector(
            physical_harm=0.2,
            rights_respect=0.82,
            fairness_equity=0.75,
            autonomy_respect=0.8,
            privacy_protection=0.7,
            societal_environmental=0.65,
            virtue_care=0.75,
            legitimacy_trust=0.8,
            epistemic_quality=0.75,
        ),
        "dominated_option": MoralVector(
            physical_harm=0.5,
            rights_respect=0.6,
            fairness_equity=0.5,
            autonomy_respect=0.5,
            privacy_protection=0.5,
            societal_environmental=0.4,
            virtue_care=0.5,
            legitimacy_trust=0.5,
            epistemic_quality=0.5,
        ),
    }

    landscape = MoralLandscape(vectors=options)

    print("Options in Landscape:")
    for name, vec in options.items():
        score = vec.to_scalar()
        print(f"  {name}: score={score:.3f}")

    # Pareto frontier
    frontier = landscape.pareto_frontier()
    print(f"\nPareto Frontier: {frontier}")

    # Dominated options
    dominated = landscape.dominated_options()
    print(f"Dominated Options: {dominated}")

    # Distance to ideal
    ideal = MoralVector.ideal()
    print("\nDistance to Ideal:")
    for name, vec in options.items():
        dist = vec.distance(ideal, "euclidean")
        print(f"  {name}: {dist:.3f}")


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    """Run all DEME 2.0 demonstrations."""
    print("\n" + "=" * 70)
    print("  DEME 2.0 DEMONSTRATION")
    print("  MoralVector-based Ethical Reasoning")
    print("=" * 70)

    demo_moral_vector_basics()
    demo_from_ethical_facts()
    demo_ethical_judgement_v2()
    demo_governance_v2()
    demo_moral_landscape()

    print_section("Summary")
    print(
        """
DEME 2.0 Key Improvements:

1. MULTI-DIMENSIONAL ASSESSMENT
   - 8+1 ethical dimensions instead of scalar score
   - Explicit trade-off visibility across dimensions
   - Domain-extensible via extensions dict

2. TIERED EM ARCHITECTURE
   - Tier 0: Constitutional (Geneva, Human Rights) - 10x weight
   - Tier 1: Core Safety - 5x weight
   - Tier 2: Rights/Fairness - 2x weight
   - Tier 3: Soft Values - 1x weight
   - Tier 4: Meta-Governance - 0.5x weight

3. EXPLICIT VETO MECHANISM
   - veto_triggered flag on judgements
   - Tier-based veto authority (Tiers 0-2 can veto)
   - veto_flags on MoralVector for constraint violations

4. PARETO-AWARE REASONING
   - Pareto frontier analysis for multi-objective decisions
   - Dominance checking without forced scalar collapse
   - Distance metrics for option comparison

5. BACKWARD COMPATIBILITY
   - normative_score property on EthicalJudgementV2
   - judgement_v1_to_v2() migration function
   - V1ToV2Adapter for legacy EMs
"""
    )


if __name__ == "__main__":
    main()
