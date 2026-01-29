"""
Triage ethics demo wired to a DEMEProfileV03, including the Geneva-base EM.

Usage:

  1. Run the dialogue to create a profile JSON, e.g.:

       cd scripts
       python ethical_dialogue_cli_v03.py ^
         --config ethical_dialogue_questions.yaml ^
         --output deme_profile_v03.json

  2. Copy or symlink deme_profile_v03.json into your working directory, then:

       python -m erisml.examples.triage_ethics_demo

  The demo will:
    - load deme_profile_v03.json,
    - construct three candidate triage options (A, B, C),
    - instantiate:
        - GenevaBaseEM-based baseline EM(s),
        - CaseStudy1TriageEM (domain EM),
        - RightsFirstEM (rights/consent EM),
      according to GovernanceConfig.base_em_ids,
    - evaluate all options with all EMs,
    - aggregate via DEME governance (with base EM veto priority),
    - and print the selected option and rationale.

This file is the canonical example of the current DEME EthicalFacts schema:
it uses the v0.2 EthicalDomains blocks from erisml.ethics.facts.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from erisml.ethics import (
    AutonomyAndAgency,
    Consequences,
    EpistemicStatus,
    EthicalFacts,
    EthicalJudgement,
    JusticeAndFairness,
    PrivacyAndDataGovernance,
    ProceduralAndLegitimacy,
    RightsAndDuties,
    SocietalAndEnvironmental,
)
from erisml.ethics.governance.aggregation import (
    DecisionOutcome,
    select_option,
)
from erisml.ethics.interop.profile_adapters import build_triage_ems_and_governance
from erisml.ethics.modules import EM_REGISTRY
from erisml.ethics.profile_v03 import DEMEProfileV03, deme_profile_v03_from_dict

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_profile(path: Path) -> DEMEProfileV03:
    """Load a DEMEProfileV03 JSON file from disk."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return deme_profile_v03_from_dict(data)


def make_demo_facts() -> Dict[str, EthicalFacts]:
    """
    Construct three demo EthicalFacts options aligned with the v0.2 schema.

      - allocate_to_patient_A:
          critical chest-pain patient who arrived later but is the most
          disadvantaged; high expected benefit and urgency, strong procedure
          and good autonomy / privacy posture.

      - allocate_to_patient_B:
          moderately ill but more stable patient; good benefit but lower
          urgency and no “most disadvantaged” flag, otherwise similar
          governance posture.

      - allocate_to_patient_C:
          rights-violating allocation with discrimination, coercion, and
          poor privacy → should be forbidden or heavily down-ranked.
    """

    # Option A – high benefit, high urgency, prioritises most disadvantaged.
    opt_a = EthicalFacts(
        option_id="allocate_to_patient_A",
        consequences=Consequences(
            expected_benefit=0.9,
            expected_harm=0.2,
            urgency=0.9,
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
        societal_and_environmental=SocietalAndEnvironmental(
            environmental_harm=0.1,
            long_term_societal_risk=0.2,
            benefits_to_future_generations=0.7,
            burden_on_vulnerable_groups=0.2,
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
    )

    # Option B – good benefit, lower urgency, not the most disadvantaged.
    opt_b = EthicalFacts(
        option_id="allocate_to_patient_B",
        consequences=Consequences(
            expected_benefit=0.8,
            expected_harm=0.2,
            urgency=0.6,
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
            distributive_pattern="utilitarian",
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
        societal_and_environmental=SocietalAndEnvironmental(
            environmental_harm=0.1,
            long_term_societal_risk=0.25,
            benefits_to_future_generations=0.6,
            burden_on_vulnerable_groups=0.25,
        ),
        procedural_and_legitimacy=ProceduralAndLegitimacy(
            followed_approved_procedure=True,
            stakeholders_consulted=True,
            decision_explainable_to_public=True,
            contestation_available=True,
        ),
        epistemic_status=EpistemicStatus(
            uncertainty_level=0.4,
            evidence_quality="medium",
            novel_situation_flag=False,
        ),
    )

    # Option C – rights violations, discrimination, coercion, poor privacy.
    opt_c = EthicalFacts(
        option_id="allocate_to_patient_C",
        consequences=Consequences(
            expected_benefit=0.7,
            expected_harm=0.4,
            urgency=0.8,
            affected_count=1,
        ),
        rights_and_duties=RightsAndDuties(
            violates_rights=True,
            has_valid_consent=False,
            violates_explicit_rule=True,
            role_duty_conflict=True,
        ),
        justice_and_fairness=JusticeAndFairness(
            discriminates_on_protected_attr=True,
            prioritizes_most_disadvantaged=False,
            distributive_pattern="other",
            exploits_vulnerable_population=True,
            exacerbates_power_imbalance=True,
        ),
        autonomy_and_agency=AutonomyAndAgency(
            has_meaningful_choice=False,
            coercion_or_undue_influence=True,
            can_withdraw_without_penalty=False,
            manipulative_design_present=True,
        ),
        privacy_and_data=PrivacyAndDataGovernance(
            privacy_invasion_level=0.8,
            data_minimization_respected=False,
            secondary_use_without_consent=True,
            data_retention_excessive=True,
            reidentification_risk=0.7,
        ),
        societal_and_environmental=SocietalAndEnvironmental(
            environmental_harm=0.3,
            long_term_societal_risk=0.6,
            benefits_to_future_generations=0.2,
            burden_on_vulnerable_groups=0.8,
        ),
        procedural_and_legitimacy=ProceduralAndLegitimacy(
            followed_approved_procedure=False,
            stakeholders_consulted=False,
            decision_explainable_to_public=False,
            contestation_available=False,
        ),
        epistemic_status=EpistemicStatus(
            uncertainty_level=0.5,
            evidence_quality="low",
            novel_situation_flag=True,
        ),
    )

    return {
        opt_a.option_id: opt_a,
        opt_b.option_id: opt_b,
        opt_c.option_id: opt_c,
    }


def print_scenario_description() -> None:
    """Print a short human-readable description of the triage scenario."""
    print("\nScenario:")
    print("  - allocate_to_patient_A:")
    print(
        "      Critical chest-pain patient who arrived later; "
        "high expected benefit, high urgency, and is the most disadvantaged."
    )
    print("  - allocate_to_patient_B:")
    print(
        "      Moderately ill but more stable patient; "
        "good expected benefit, lower urgency, not the most disadvantaged."
    )
    print("  - allocate_to_patient_C:")
    print(
        "      Rights-violating allocation option; involves discrimination "
        "and breaches explicit rules/consent."
    )


def print_option_results(
    option_id: str,
    judgements: List[EthicalJudgement],
    aggregate: EthicalJudgement,
) -> None:
    """Pretty-print per-EM judgements plus the governance aggregate."""
    print(f"\n--- Option: {option_id} ---")
    for j in judgements:
        print(
            f"[EM={j.em_name:<24}] verdict={j.verdict:<15} "
            f"score={j.normative_score:.3f}"
        )
        for reason in j.reasons:
            print(f"    - {reason}")

    print(
        f"[AGG governance] verdict={aggregate.verdict:<15} "
        f"score={aggregate.normative_score:.3f}"
    )

    meta = aggregate.metadata or {}
    forbidden = meta.get("forbidden", False)
    forbidden_by = meta.get("forbidden_by", [])
    vetoed_by = meta.get("vetoed_by", [])

    if forbidden:
        print("    * Marked FORBIDDEN by governance.")
    if forbidden_by:
        print("    * Forbidden by EM(s): " + ", ".join(sorted(set(forbidden_by))))
    if vetoed_by:
        print("    * Veto EM(s): " + ", ".join(sorted(set(vetoed_by))))


# ---------------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------------


def run_demo(profile_path: Path) -> None:
    print("=== Triage Ethics Demo (DEMEProfileV03 + GenevaBaseEM) ===\n")

    profile = load_profile(profile_path)
    triage_em, rights_em, gov_cfg = build_triage_ems_and_governance(profile)

    facts_by_option = make_demo_facts()
    option_ids = list(facts_by_option.keys())

    print(
        f"Loaded profile: {profile.name} "
        f"(stakeholder={profile.stakeholder_label}, tags={profile.tags})"
    )
    print("Candidate options:")
    for oid in option_ids:
        print(f"  - {oid}")

    # New: print a short scenario description for human/audit readers.
    print_scenario_description()

    # Instantiate EMs: base Geneva EM(s) plus domain + rights EMs.
    ems = {
        "case_study_1_triage": triage_em,
        "rights_first_compliance": rights_em,
    }

    # Add base EMs from governance config, if present.
    for base_id in getattr(gov_cfg, "base_em_ids", []):
        em_cls = EM_REGISTRY.get(base_id)
        if em_cls is None:
            print(f"[warn] base_em_id '{base_id}' not found in EM_REGISTRY.")
            continue
        ems[base_id] = em_cls()

    print("\nActive EMs in this demo:")
    for name in ems.keys():
        print(f"  - {name}")

    all_judgements: Dict[str, List[EthicalJudgement]] = defaultdict(list)

    # Collect per-option judgements from all EMs.
    for oid, facts in facts_by_option.items():
        for em_name, em in ems.items():
            j = em.judge(facts)
            all_judgements[oid].append(j)

    # Use the governance layer to aggregate and select an option.
    decision: DecisionOutcome = select_option(all_judgements, gov_cfg)

    # Per-option aggregates for display.
    for oid in option_ids:
        per_option_j = all_judgements.get(oid, [])
        agg_j = decision.aggregated_judgements.get(oid)
        if agg_j is None:
            continue
        print_option_results(oid, per_option_j, agg_j)

    print("\n=== Governance Outcome ===")
    if decision.selected_option_id is None:
        print("No permissible option selected.")
    else:
        print(f"Selected option: '{decision.selected_option_id}'")
    print(f"Ranked options (eligible): {decision.ranked_options}")
    print(f"Forbidden options: {decision.forbidden_options}")
    print("Rationale:")
    print(f"  {decision.rationale}")


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    profile_path = Path("deme_profile_v03.json")
    if not profile_path.exists():
        raise SystemExit(
            "No deme_profile_v03.json found in current directory.\n"
            "Run 'scripts/ethical_dialogue_cli_v03.py' first to create one."
        )

    run_demo(profile_path)


if __name__ == "__main__":
    main()
