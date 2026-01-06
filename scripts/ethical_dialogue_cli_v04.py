#!/usr/bin/env python
"""
ethical_dialogue_cli_v04.py

Interactive, YAML-driven DEME ethics dialogue that builds a DEMEProfileV03.

Refinements in this version:
  - Uses the internal profile name to derive a default output filename
    (e.g., 'Jain_Household_v1.deme_profile_v03.json') when --output is
    not explicitly set.
  - Wires through an extended set of HardVetoes flags, driven by the
    updated ethical_dialogue_questions.yaml (including Greek-myth-inspired
    scenes).
  - Keeps lexical_layers and override_graph support from v03.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict
from typing import Any, Dict, List

import yaml  # pip install pyyaml

from erisml.ethics.profile_v03 import (
    DEMEProfileV03,
    PrinciplismWeights,
    TrustworthinessWeights,
    DEMEDimensionWeights,
    RiskAttitudeProfile,
    DimensionRiskTolerance,
    RiskAppetite,
    HardVetoes,
    GovernanceExpectations,
    PatternConstraint,
    PatternConstraintKind,
    LexicalLayer,
    OverrideEdge,
    OverrideMode,
    deme_profile_v03_to_dict,
)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------


def ask_choice(prompt: str, options: List[str]) -> int:
    print()
    print(prompt)
    for i, opt in enumerate(options, start=1):
        print(f"  {i}. {opt}")
    while True:
        raw = input("Enter choice number: ").strip()
        try:
            idx = int(raw)
        except ValueError:
            print("Please enter a valid number.")
            continue
        if 1 <= idx <= len(options):
            return idx - 1
        print(f"Please enter a number between 1 and {len(options)}.")


def ask_yes_no(prompt: str, default: bool | None = None) -> bool:
    while True:
        if default is True:
            suffix = " [Y/n]: "
        elif default is False:
            suffix = " [y/N]: "
        else:
            suffix = " [y/n]: "
        raw = input(prompt + suffix).strip().lower()
        if not raw and default is not None:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("Please answer 'y' or 'n'.")


def ask_free_text(prompt: str) -> str:
    print()
    print(prompt)
    print("You may leave this blank and press Enter.")
    return input("> ").strip()


# ---------------------------------------------------------------------------
# Dialogue pieces
# ---------------------------------------------------------------------------


def intro(config: Dict[str, Any]) -> Dict[str, Any]:
    meta_cfg = config.get("meta", {})
    title = meta_cfg.get("title", "DEME Ethics Dialogue")
    desc = meta_cfg.get("description", "")

    print("=" * 72)
    print(f" {title}")
    print("=" * 72)
    if desc:
        print(desc)
        print()

    print(
        "This dialogue configures the value stance of a single stakeholder\n"
        "group, which will become a DEMEProfileV03.\n"
    )

    name = input(
        "Internal name for this EM profile (e.g., 'Jain_Household_v1'): "
    ).strip()
    if not name:
        name = "EM_Profile_V03"

    stakeholder = ask_free_text(
        "Who does this profile represent? (e.g., 'patients_and_public', "
        "'hospital_ethics_board', 'Jain_community')"
    )
    if not stakeholder:
        stakeholder = "unspecified_stakeholder"

    domain = ask_free_text(
        "Optional domain/context label "
        "(e.g., 'clinical_triage', 'domestic', 'maritime', 'GAI_content'):"
    )
    if not domain:
        domain = None

    description = ask_free_text(
        "Brief description of this profile (what system/context it applies to):"
    )

    domain_options = [
        "domestic",
        "clinical",
        "maritime",
        "urban_logistics",
        "generic",
    ]
    print()
    print("Select domain scope (one or more, comma-separated indices).")
    for i, opt in enumerate(domain_options, start=1):
        print(f"  {i}. {opt}")
    raw = input("Enter selection (e.g. '1,3' or press Enter for 'generic'): ").strip()
    if not raw:
        domain_scope = ["generic"]
    else:
        selected: List[str] = []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                idx = int(part)
            except ValueError:
                continue
            if 1 <= idx <= len(domain_options):
                selected.append(domain_options[idx - 1])
        domain_scope = selected or ["generic"]

    return {
        "name": name,
        "stakeholder": stakeholder,
        "domain": domain,
        "description": description,
        "domain_scope": domain_scope,
    }


def initialize_dimension_scores(config: Dict[str, Any]) -> Dict[str, float]:
    dims_cfg = config["dimensions"]
    scores: Dict[str, float] = {}
    for dim_key, dim_info in dims_cfg.items():
        scores[dim_key] = float(dim_info.get("base_weight", 1.0))
    return scores


def normalize(scores: Dict[str, float]) -> Dict[str, float]:
    total = sum(scores.values())
    if total <= 0:
        n = len(scores) or 1
        return {k: 1.0 / n for k in scores}
    return {k: v / total for k, v in scores.items()}


def ask_high_level(config: Dict[str, Any], scores: Dict[str, float]) -> None:
    hl = config["high_level"]
    prompt = hl["prompt"]
    options = hl["options"]
    texts = [opt["text"] for opt in options]
    idx = ask_choice(prompt, texts)
    chosen = options[idx]
    dim_key = chosen["dimension"]
    if dim_key in scores:
        scores[dim_key] += 1.5


def ask_pairwise(config: Dict[str, Any], scores: Dict[str, float]) -> None:
    pt_cfg = config.get("pairwise_tradeoffs", [])
    scale_cfg = config.get("pairwise_scale", {})
    scale_prompt = scale_cfg.get("prompt", "")
    scale_opts = scale_cfg.get("options", [])
    if not pt_cfg or not scale_opts:
        return

    scale_texts = [o["text"] for o in scale_opts]

    for trade in pt_cfg:
        dim_a = trade["dim_a"]
        dim_b = trade["dim_b"]
        desc = trade["description"]
        print()
        print("-" * 72)
        print(desc)
        idx = ask_choice(scale_prompt, scale_texts)
        value = int(scale_opts[idx]["value"])
        if value < 0:
            scores[dim_a] = scores.get(dim_a, 0.0) + abs(value) * 0.5
        elif value > 0:
            scores[dim_b] = scores.get(dim_b, 0.0) + abs(value) * 0.5


def ask_hard_vetoes(config: Dict[str, Any]) -> Dict[str, bool]:
    hv_cfg = config.get("hard_vetoes", [])
    flags: Dict[str, bool] = {}
    if hv_cfg:
        print()
        print("-" * 72)
        print("Hard 'never do this' questions\n")

    for item in hv_cfg:
        vid = item["id"]
        prompt = item["prompt"]
        default = item.get("default", True)
        flags[vid] = ask_yes_no(prompt, default=default)

    return flags


def ask_override_mode(config: Dict[str, Any]) -> OverrideMode:
    op_cfg = config["override_policy"]
    prompt = op_cfg["prompt"]
    options = op_cfg["options"]  # mapping id -> {text}

    keys = list(options.keys())
    texts = [options[k]["text"] for k in keys]
    print()
    print("-" * 72)
    idx = ask_choice(prompt, texts)
    chosen_key = keys[idx]
    if chosen_key == "rights_first":
        return OverrideMode.RIGHTS_FIRST
    if chosen_key == "consequences_first":
        return OverrideMode.CONSEQUENCES_FIRST
    return OverrideMode.BALANCED_CASE_BY_CASE


def ask_risk_appetite() -> RiskAttitudeProfile:
    print()
    print("-" * 72)
    print("Overall risk appetite\n")
    idx = ask_choice(
        "In general, how cautious vs bold should this system be when the "
        "stakes are uncertain?",
        [
            "Very cautious: avoid risk even if it means missing opportunities.",
            "Balanced: accept some risk when benefits are clear.",
            "More tolerant of risk: willing to act with less certainty.",
        ],
    )
    if idx == 0:
        appetite = RiskAppetite.RISK_AVERSE
        max_overall = 0.2
    elif idx == 2:
        appetite = RiskAppetite.RISK_TOLERANT
        max_overall = 0.5
    else:
        appetite = RiskAppetite.BALANCED
        max_overall = 0.3

    tolerances = DimensionRiskTolerance(
        safety=0.1 if appetite == RiskAppetite.RISK_AVERSE else 0.2,
        rights=0.05 if appetite == RiskAppetite.RISK_AVERSE else 0.1,
        fairness=0.15,
        privacy=0.15,
        information_integrity=0.2,
        security_resilience=0.2,
        environmental=0.2,
    )

    return RiskAttitudeProfile(
        appetite=appetite,
        max_overall_risk=max_overall,
        tolerances=tolerances,
        escalate_near_threshold=True,
        escalation_margin=0.05,
    )


# ---------------------------------------------------------------------------
# Derivation helpers
# ---------------------------------------------------------------------------


def derive_deme_dimensions(norm_scores: Dict[str, float]) -> DEMEDimensionWeights:
    return DEMEDimensionWeights(
        safety=norm_scores.get("safety", 0.0),
        autonomy_respect=norm_scores.get("autonomy", 0.0),
        fairness_equity=norm_scores.get("fairness", 0.0),
        privacy_confidentiality=norm_scores.get("privacy", 0.0),
        environment_societal=norm_scores.get("environment", 0.0),
        rule_following_legality=norm_scores.get("rule_following", 0.0),
        priority_for_vulnerable=norm_scores.get("vulnerable_priority", 0.0),
        trust_relationships=0.05,
    )


def derive_principlism(dim: DEMEDimensionWeights) -> PrinciplismWeights:
    beneficence = dim.safety + 0.5 * dim.priority_for_vulnerable
    non_maleficence = dim.safety + 0.5 * dim.privacy_confidentiality
    autonomy = dim.autonomy_respect + 0.5 * dim.privacy_confidentiality
    justice = dim.fairness_equity + 0.5 * dim.priority_for_vulnerable

    total = beneficence + non_maleficence + autonomy + justice or 1.0
    return PrinciplismWeights(
        beneficence=beneficence / total,
        non_maleficence=non_maleficence / total,
        autonomy=autonomy / total,
        justice=justice / total,
    )


def derive_trustworthiness(dim: DEMEDimensionWeights) -> TrustworthinessWeights:
    valid_reliable = 0.2
    safe = dim.safety
    secure_resilient = dim.rule_following_legality * 0.5 + 0.1
    accountable_transparent = dim.rule_following_legality * 0.5 + 0.1
    explainable_interpretable = 0.1
    privacy_enhanced = dim.privacy_confidentiality
    fair_bias_managed = dim.fairness_equity

    total = (
        valid_reliable
        + safe
        + secure_resilient
        + accountable_transparent
        + explainable_interpretable
        + privacy_enhanced
        + fair_bias_managed
        or 1.0
    )

    return TrustworthinessWeights(
        valid_reliable=valid_reliable / total,
        safe=safe / total,
        secure_resilient=secure_resilient / total,
        accountable_transparent=accountable_transparent / total,
        explainable_interpretable=(
            explaineable_interpretable
            if (explaineable_interpretable := explainable_interpretable) or True
            else 0.0
        ),  # keep lint tools happy without extra temp vars
        privacy_enhanced=privacy_enhanced / total,
        fair_bias_managed=fair_bias_managed / total,
    )


def derive_hard_vetoes(flags: Dict[str, bool]) -> HardVetoes:
    """
    Map YAML flag ids to the HardVetoes structure.

    Any veto not explicitly wired here will retain its default value
    as defined in HardVetoes.
    """
    return HardVetoes(
        never_catastrophic_safety_harm=flags.get(
            "never_catastrophic_safety_harm", True
        ),
        never_intentional_serious_harm=flags.get(
            "never_intentional_serious_harm", True
        ),
        never_discriminate_protected_groups=flags.get(
            "never_discriminate_protected_groups", True
        ),
        never_violate_explicit_consent=flags.get(
            "never_violate_explicit_consent_low_stakes", True
        ),
        never_systematic_privacy_violation=flags.get(
            "never_systematic_privacy_violation", True
        ),
        never_mass_surveillance_private_spaces=flags.get(
            "never_mass_surveillance_in_private_spaces", True
        ),
        never_persistent_misinfo_disinfo_campaigns=flags.get(
            "never_persistent_misinfo_disinfo_campaigns", True
        ),
        never_child_sexual_abuse_or_exploitative_content=flags.get(
            "never_child_sexual_abuse_or_exploitative_content", True
        ),
        never_illegal_content_even_if_utility_high=flags.get(
            "never_illegal_content_even_if_utility_high", True
        ),
        never_needless_harm_to_non_human_life=flags.get(
            "never_needless_harm_to_non_human_life", True
        ),
        never_fabricate_critical_evidence=flags.get(
            "never_fabricate_critical_evidence", True
        ),
        never_impersonate_real_person_without_consent=flags.get(
            "never_impersonate_real_person_without_consent", True
        ),
    )


def derive_pattern_constraints(flags: Dict[str, bool]) -> List[PatternConstraint]:
    """
    Derive a small set of structured pattern constraints based on
    selected hard vetoes. This is intentionally conservative: only
    a few vetoes are expressed as explicit EthicalFacts expressions.
    """
    pcs: List[PatternConstraint] = []

    if flags.get("never_intentional_serious_harm", True):
        pcs.append(
            PatternConstraint(
                name="forbid_high_expected_harm",
                kind=PatternConstraintKind.FORBID_WHEN,
                expression="consequences.expected_harm >= 0.8",
                rationale="Avoid options with very high expected serious harm.",
            )
        )

    if flags.get("never_discriminate_protected_groups", True):
        pcs.append(
            PatternConstraint(
                name="forbid_protected_attr_discrimination",
                kind=PatternConstraintKind.FORBID_WHEN,
                expression="justice_and_fairness.discriminates_on_protected_attr == true",
                rationale="Do not discriminate on protected attributes.",
            )
        )

    if flags.get("never_needless_harm_to_non_human_life", True):
        pcs.append(
            PatternConstraint(
                name="avoid_needless_non_human_harm",
                kind=PatternConstraintKind.FORBID_WHEN,
                expression=(
                    "societal_and_environmental.harms_non_human_life == true "
                    "&& societal_and_environmental.reasonable_alternative_available == true"
                ),
                rationale="Avoid needless harm to non-human life when a reasonable alternative exists.",
            )
        )

    # Additional pattern constraints for other vetoes could be added here
    # as the EthicalFacts schema evolves.

    return pcs


def derive_lexical_and_overrides(
    override_mode: OverrideMode,
) -> tuple[List[LexicalLayer], List[OverrideEdge]]:
    """
    Heuristic mapping from override_mode to a small lexical hierarchy and
    a DAG of overrides. This can be refined later or made configurable.
    """

    lexical_layers: List[LexicalLayer] = []
    override_graph: List[OverrideEdge] = []

    if override_mode == OverrideMode.RIGHTS_FIRST:
        lexical_layers = [
            LexicalLayer(
                name="rights_and_duties",
                principles=["autonomy", "rights", "rule_following_legality"],
                hard_stop=True,
            ),
            LexicalLayer(
                name="welfare",
                principles=["safety", "priority_for_vulnerable"],
                hard_stop=False,
            ),
            LexicalLayer(
                name="justice_and_commons",
                principles=["fairness", "environment"],
                hard_stop=False,
            ),
        ]
        # Allow safety to override autonomy only in extremely urgent,
        # low-uncertainty situations.
        override_graph.append(
            OverrideEdge(
                higher="non_maleficence",
                lower="autonomy",
                context_condition=(
                    "consequences.urgency >= 0.95 "
                    "&& epistemic_status.uncertainty_level <= 0.4"
                ),
                strength=0.9,
            )
        )

    elif override_mode == OverrideMode.CONSEQUENCES_FIRST:
        lexical_layers = [
            LexicalLayer(
                name="welfare",
                principles=["safety", "priority_for_vulnerable"],
                hard_stop=True,
            ),
            LexicalLayer(
                name="rights_and_duties",
                principles=["autonomy", "rights", "rule_following_legality"],
                hard_stop=False,
            ),
            LexicalLayer(
                name="justice_and_commons",
                principles=["fairness", "environment"],
                hard_stop=False,
            ),
        ]
        override_graph.append(
            OverrideEdge(
                higher="beneficence",
                lower="autonomy",
                context_condition=(
                    "consequences.expected_benefit - consequences.expected_harm >= 0.6"
                ),
                strength=0.8,
            )
        )

    else:  # BALANCED_CASE_BY_CASE
        lexical_layers = []
        override_graph = []

    return lexical_layers, override_graph


# ---------------------------------------------------------------------------
# Main dialogue flow
# ---------------------------------------------------------------------------


def run_dialogue(config: Dict[str, Any]) -> DEMEProfileV03:
    ident = intro(config)

    scores = initialize_dimension_scores(config)
    ask_high_level(config, scores)
    ask_pairwise(config, scores)
    norm_scores = normalize(scores)

    deme_dims = derive_deme_dimensions(norm_scores)
    principlism = derive_principlism(deme_dims)
    trustworthiness = derive_trustworthiness(deme_dims)

    hv_flags = ask_hard_vetoes(config)
    hard_vetoes = derive_hard_vetoes(hv_flags)
    override_mode = ask_override_mode(config)
    risk_attitude = ask_risk_appetite()
    pattern_constraints = derive_pattern_constraints(hv_flags)

    notes_prompt = config.get("notes_prompt", "Any additional notes?")
    notes = ask_free_text(notes_prompt)

    lexical_layers, override_graph = derive_lexical_and_overrides(override_mode)

    governance_expectations = GovernanceExpectations(
        expects_govern_function=True,
        expects_map_function=True,
        expects_measure_function=True,
        expects_manage_function=True,
        requires_documented_risk_register=True,
        requires_incident_reporting_process=True,
        requires_human_oversight_roles_defined=True,
        requires_tevv_for_high_risk_use=True,
        ai_rmf_profile_id=None,
    )

    profile = DEMEProfileV03(
        name=ident["name"],
        description=ident["description"],
        stakeholder_label=ident["stakeholder"],
        domain=ident["domain"],
        principlism=principlism,
        trustworthiness=trustworthiness,
        deme_dimensions=deme_dims,
        risk_attitude=risk_attitude,
        override_mode=override_mode,
        lexical_layers=lexical_layers,
        override_graph=override_graph,
        hard_vetoes=hard_vetoes,
        pattern_constraints=pattern_constraints,
        governance_expectations=governance_expectations,
        tags=ident["domain_scope"],
        notes=notes,
    )

    return profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interactive DEME ethics dialogue (V03 → DEMEProfileV03 JSON)."
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="ethical_dialogue_questions.yaml",
        help="YAML config file with narrative questions.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="em_profile_v03.json",
        help=(
            "Path to write resulting profile JSON. If left as the default "
            "value, a name will be derived from the internal EM profile name, "
            "e.g. 'Jain_Household_v1.deme_profile_v03.json'."
        ),
    )
    return parser.parse_args()


def derive_output_path(requested_output: str, profile_name: str) -> str:
    """
    If the user left --output at its default value, derive a filename
    from the internal profile name; otherwise, honor the explicit path.
    """
    if requested_output != "em_profile_v03.json":
        return requested_output

    base = profile_name or "EM_Profile_V03"
    # Make it filesystem-friendly: letters, digits, underscore, dash, dot
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", base).strip("_")
    if not safe:
        safe = "EM_Profile_V03"
    return f"{safe}.deme_profile_v03.json"


def main() -> None:
    args = parse_args()
    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    profile = run_dialogue(config)
    data = deme_profile_v03_to_dict(profile)

    output_path = derive_output_path(args.output, profile.name)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 72)
    print(f"DEMEProfileV03 written to: {output_path}")
    print("DEME dimension weights:")
    for k, v in asdict(profile.deme_dimensions).items():
        print(f"  {k:24s}: {v:.3f}")
    print("Principlism weights:")
    for k, v in asdict(profile.principlism).items():
        print(f"  {k:24s}: {v:.3f}")
    print("Override mode:", profile.override_mode.value)
    print("Lexical layers:")
    for layer in profile.lexical_layers:
        print(
            f"  - {layer.name}: principles={layer.principles}, "
            f"hard_stop={layer.hard_stop}"
        )
    print("Hard vetoes enabled:")
    for field_name, value in asdict(profile.hard_vetoes).items():
        if value:
            print(f"  - {field_name}")
    print("=" * 72)


if __name__ == "__main__":
    main()
