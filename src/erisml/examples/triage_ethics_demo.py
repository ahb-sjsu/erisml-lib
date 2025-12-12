# src/erisml/examples/triage_ethics_demo.py

"""
Triage ethics demo wired to a DEMEProfileV03.

Usage:

  1. Run the dialogue to create a profile JSON, e.g.:

       python scripts/ethical_dialogue_cli_v03.py \
         --config ethical_dialogue_questions.yaml \
         --output em_profile_v03.json

  2. Then run:

       python -m erisml.examples.triage_ethics_demo

  The demo will:
    - load em_profile_v03.json,
    - construct three candidate triage options (A, B, C),
    - evaluate them with CaseStudy1TriageEM + RightsFirstEM
      configured from the DEME profile,
    - aggregate via DEME governance,
    - and print the selected option and rationale.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from erisml.ethics import (
    EthicalFacts,
    Consequences,
    RightsAndDuties,
    JusticeAndFairness,
    AutonomyAndAgency,
    PrivacyAndDataGovernance,
    SocietalAndEnvironmental,
    ProceduralAndLegitimacy,
    EpistemicStatus,
    EthicalJudgement,
    aggregate_judgements,
    select_option,
)
from erisml.ethics.governance.aggregation import DecisionOutcome
from erisml.ethics.interop.profile_adapters import (
    build_triage_ems_and_governance,
)
from erisml.ethics.profile_v03 import (
    DEMEProfileV03,
    deme_profile_v03_from_dict,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_profile(path: Path) -> DEMEProfileV03:
    """Load a DEMEProfileV03 JSON file from disk."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return deme_profile_v03_from_dict(data)


def make_demo_facts() -> Dict[str, EthicalFacts]:
    """
    Construct three demo EthicalFacts options:

      - allocate_to_patient_A: high benefit, high urgency, good fairness.
      - allocate_to_patient_B: good benefit but lower urgency.
      - allocate_to_patient_C: rights / rule violation → should be forbidden.
    """

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
        ),
        autonomy_and_agency=AutonomyAndAgency(
            supports_voluntary_choice=True,
            coerces_or_manipulates=False,
            respects_opt_out=True,
        ),
        privacy_and_data_governance=PrivacyAndDataGovernance(
            uses_minimum_necessary_data=True,
            shares_data_externally=False,
            has_strong_protections=True,
        ),
        societal_and_environmental=SocietalAndEnvironmental(
            impacts_public_trust=True,
            harms_non_human_life=False,
            reasonable_alternative_available=False,
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
        ),
        autonomy_and_agency=AutonomyAndAgency(
            supports_voluntary_choice=True,
            coerces_or_manipulates=False,
            respects_opt_out=True,
        ),
        privacy_and_data_governance=PrivacyAndDataGovernance(
            uses_minimum_necessary_data=True,
            shares_data_externally=False,
            has_strong_protections=True,
        ),
        societal_and_environmental=SocietalAndEnvironmental(
            impacts_public_trust=True,
            harms_non_human_life=False,
            reasonable_alternative_available=True,
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
        ),
        autonomy_and_agency=AutonomyAndAgency(
            supports_voluntary_choice=False,
            coerces_or_manipulates=True,
            respects_opt_out=False,
        ),
        privacy_and_data_governance=PrivacyAndDataGovernance(
            uses_minimum_necessary_data=False,
            shares_data_externally=True,
            has_strong_protections=False,
        ),
        societal_and_environmental=SocietalAndEnvironmental(
            impacts_public_trust=False,
            harms_non_human_life=False,
            reasonable_alternative_available=True,
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


def print_option_results(
    option_id: str,
    judgements: List[EthicalJudgement],
    aggregate: DecisionOutcome,
) -> None:
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
    for line in aggregate.details.splitlines():
        print(f"    * {line}")


# ---------------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------------


def run_demo(profile_path: Path) -> None:
    print("=== Triage Ethics Demo (DEMEProfileV03) ===\n")

    profile = load_profile(profile_path)
    triage_em, rights_em, gov_cfg = build_triage_ems_and_governance(profile)

    facts_by_option = make_demo_facts()
    option_ids = list(facts_by_option.keys())

    print("Candidate options:")
    for oid in option_ids:
        print(f"  - {oid}")

    from collections import defaultdict

    all_judgements: Dict[str, List[EthicalJudgement]] = defaultdict(list)
    outcomes: Dict[str, DecisionOutcome] = {}

    for oid, facts in facts_by_option.items():
        j1 = triage_em.judge(facts)
        j2 = rights_em.judge(facts)
        all_judgements[oid].extend([j1, j2])

        agg = aggregate_judgements(oid, all_judgements[oid], gov_cfg)
        outcomes[oid] = agg
        print_option_results(oid, all_judgements[oid], agg)

    selected = select_option(outcomes, gov_cfg)
    forbidden = [oid for oid, d in outcomes.items() if d.verdict == "forbid"]

    print("\n=== Governance Outcome ===")
    if selected is None:
        print("No permissible option selected.")
    else:
        print(f"Selected option: '{selected}'")
    print(f"Ranked options: { [oid for oid in option_ids if oid not in forbidden] }")
    print(f"Forbidden options: {forbidden}")
    print(
        "Rationale:"
        f"\n  Selected option '{selected}' based on aggregated normative scores "
        f"and GovernanceConfig. Forbidden options: {forbidden}."
    )


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    profile_path = Path("em_profile_v03.json")
    if not profile_path.exists():
        raise SystemExit(
            "No em_profile_v03.json found in current directory.\n"
            "Run 'ethical_dialogue_cli_v03.py' first to create one."
        )

    run_demo(profile_path)


if __name__ == "__main__":
    main()
