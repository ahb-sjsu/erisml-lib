#!/usr/bin/env python
"""
ethical_dialogue_cli.py

Interactive, YAML-driven DEME ethics dialogue that builds a
DEMEProfileV01 instance and writes it as JSON.

This is a v2 builder that targets the richer EM profile schema defined in
`erisml.ethics.domain.em_profile.DEMEProfileV01`.
"""

from __future__ import annotations

import argparse
import json
from typing import Dict, List, Any

import yaml  # pip install pyyaml

from erisml.ethics.domain.em_profile import (
    DEMEProfileV01,
    Metadata,
    Provenance,
    PrincipleAlignment,
    PrinciplismAlignment,
    AIPrinciplesAlignment,
    RiskAttitude,
    SafetyPolicy,
    AutonomyPolicy,
    FairnessPolicy,
    VulnerablePriorityPolicy,
    PrivacyPolicy,
    EnvironmentPolicy,
    RuleFollowingPolicy,
    TransparencyPolicy,
    OversightPolicy,
    Constraints,
    PatternCondition,
    PatternEffect,
    PatternRule,
    OverridePolicy,
)


# ---------- CLI helpers (menus, prompts) ----------


def ask_choice(prompt: str, options: List[str]) -> int:
    """
    Present a numbered menu and return the chosen index (0-based).
    """
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
    """
    Ask a yes/no question, return True/False.
    """
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
    """
    Ask for free text. Empty is allowed.
    """
    print()
    print(prompt)
    print("You may leave this blank and press Enter.")
    return input("> ").strip()


# ---------- Dialogue steps ----------


def intro(config: dict) -> tuple[str, str, str, List[str]]:
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
        "This dialogue can be answered by an individual or a committee.\n"
        "If you are a group, answer according to your consensus or majority view.\n"
    )

    name = input(
        "Internal name for this EM profile (e.g., 'Jain_Household_v1'): "
    ).strip()
    if not name:
        name = "EM_Profile_1"

    display_name = ask_free_text(
        "Human-readable name (e.g., 'Jain Household Domestic Robot EM')"
    )
    if not display_name:
        display_name = name

    stakeholder_group = ask_free_text(
        "Who does this profile represent? (e.g., 'Local Jain community working group')"
    )

    # Domain scope: allow multiple selection via comma-separated indices.
    domain_options = [
        "domestic",
        "clinical",
        "maritime",
        "urban_logistics",
        "generic",
    ]
    print()
    print("Select domain scope for this EM (one or more, comma-separated indices).")
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

    return name, display_name, stakeholder_group, domain_scope


def initialize_weights(config: dict) -> Dict[str, float]:
    dimensions = config["dimensions"]
    weights: Dict[str, float] = {}
    for dim_key, dim_cfg in dimensions.items():
        weights[dim_key] = float(dim_cfg.get("base_weight", 1.0))
    return weights


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        n = len(weights) or 1
        return {k: 1.0 / n for k in weights}
    return {k: v / total for k, v in weights.items()}


def ask_high_level_orientation(
    config: dict,
    weights: Dict[str, float],
) -> None:
    high_cfg = config["high_level"]
    prompt = high_cfg["prompt"]
    options = high_cfg["options"]

    option_texts = [opt["text"] for opt in options]
    idx = ask_choice(prompt, option_texts)
    chosen = options[idx]
    dim_key = chosen["dimension"]

    if dim_key not in weights:
        print(
            f"[WARN] Dimension '{dim_key}' from high_level not in dimensions; skipping boost."
        )
        return

    # Boost chosen dimension
    weights[dim_key] += 1.5


def ask_pairwise_tradeoffs(
    config: dict,
    weights: Dict[str, float],
) -> None:
    pt_cfg = config.get("pairwise_tradeoffs", [])
    scale_cfg = config.get("pairwise_scale", {})
    scale_prompt = scale_cfg.get("prompt", "How do you lean overall on this tradeoff?")
    scale_options = scale_cfg.get("options", [])

    if not pt_cfg or not scale_options:
        return

    for trade in pt_cfg:
        dim_a = trade["dim_a"]
        dim_b = trade["dim_b"]
        description = trade["description"]

        print()
        print("-" * 72)
        print(description)
        choice_texts = [opt["text"] for opt in scale_options]
        idx = ask_choice(scale_prompt, choice_texts)
        value = int(scale_options[idx]["value"])

        # value in [-2..+2]; negative -> favor dim_a, positive -> favor dim_b
        if value < 0:
            weights[dim_a] = weights.get(dim_a, 0.0) + abs(value) * 0.5
        elif value > 0:
            weights[dim_b] = weights.get(dim_b, 0.0) + abs(value) * 0.5


def ask_hard_vetoes(config: dict) -> Dict[str, bool]:
    hv_cfg = config.get("hard_vetoes", [])
    flags: Dict[str, bool] = {}

    if hv_cfg:
        print()
        print("-" * 72)
        print("Hard 'Never Do This' Questions")
        print(
            "For each statement, answer whether the system should treat it as something\n"
            "that is never acceptable (a hard veto), except perhaps in extreme cases.\n"
        )

    for item in hv_cfg:
        vid = item["id"]
        prompt = item["prompt"]
        default = item.get("default", True)
        answer = ask_yes_no(prompt, default=default)
        flags[vid] = answer

    return flags


def ask_override_mode(config: dict) -> OverridePolicy:
    op_cfg = config["override_policy"]
    prompt = op_cfg["prompt"]
    options = op_cfg["options"]  # mapping id -> {text}

    keys = list(options.keys())
    texts = [options[k]["text"] for k in keys]

    print()
    print("-" * 72)
    idx = ask_choice(prompt, texts)
    chosen_key = keys[idx]

    # Basic defaults; can be refined later or configured via YAML.
    if chosen_key == "rights_first":
        requires_escalation = True
    elif chosen_key == "consequences_first":
        requires_escalation = False
    else:
        requires_escalation = True

    return OverridePolicy(
        mode=chosen_key,  # type: ignore[arg-type]
        requires_human_escalation=requires_escalation,
        document_override_reason=True,
    )


def derive_principle_alignment(
    dim_weights: Dict[str, float],
) -> PrincipleAlignment:
    """
    Heuristic mapping from core DEME dimension weights to principlism and AI principles.

    This is deliberately simple and can be refined later.
    """
    safety = dim_weights.get("safety", 0.0)
    autonomy = dim_weights.get("autonomy", 0.0)
    fairness = dim_weights.get("fairness", 0.0)
    privacy_w = dim_weights.get("privacy", 0.0)
    env = dim_weights.get("environment", 0.0)
    vulnerable = dim_weights.get("vulnerable_priority", 0.0)

    principlism = PrinciplismAlignment(
        autonomy=autonomy,
        beneficence=0.5 * safety + 0.5 * vulnerable,
        nonmaleficence=safety,
        justice=0.5 * fairness + 0.5 * vulnerable,
    )

    ai_principles = AIPrinciplesAlignment(
        fairness=fairness,
        privacy=privacy_w,
        safety_robustness=safety,
        transparency=0.5,  # neutral default
        accountability=0.5,
        sustainability=env,
    )

    return PrincipleAlignment(
        principlism=principlism,
        ai_principles=ai_principles,
    )


def derive_policy_blocks_from_weights(
    dim_weights: Dict[str, float],
    hard_veto_flags: Dict[str, bool],
) -> Dict[str, Any]:
    """
    Produce policy block instances from dimension weights and hard veto answers.

    This is heuristic and intended as a reasonable default mapping that
    can be refined through governance.
    """
    safety_w = dim_weights.get("safety", 0.0)
    autonomy_w = dim_weights.get("autonomy", 0.0)
    fairness_w = dim_weights.get("fairness", 0.0)
    privacy_w = dim_weights.get("privacy", 0.0)
    env_w = dim_weights.get("environment", 0.0)
    vuln_w = dim_weights.get("vulnerable_priority", 0.0)

    # Risk & safety
    if safety_w >= 0.25:
        min_harm = 0.2
        escalate_uncert = 0.5
    elif safety_w >= 0.15:
        min_harm = 0.3
        escalate_uncert = 0.7
    else:
        min_harm = 0.4
        escalate_uncert = 0.8

    safety_policy = SafetyPolicy(
        min_acceptable_harm_score=min_harm,
        prefer_lower_risk_even_if_less_benefit=True,
        escalate_when_uncertainty_exceeds=escalate_uncert,
    )

    # Autonomy
    respect_low_stakes = autonomy_w >= 0.1
    allow_override_high = True
    autonomy_policy = AutonomyPolicy(
        respect_refusal_in_low_stakes=respect_low_stakes,
        allow_override_in_high_stakes=allow_override_high,
        override_requires_human_confirmation=True,
    )

    # Fairness & vulnerable priority
    if fairness_w >= 0.25:
        avoid_disc = "strict"
    elif fairness_w >= 0.15:
        avoid_disc = "moderate"
    else:
        avoid_disc = "moderate"

    if vuln_w >= 0.2:
        vuln_strength = "strong"
    elif vuln_w >= 0.1:
        vuln_strength = "moderate"
    elif vuln_w > 0.0:
        vuln_strength = "mild"
    else:
        vuln_strength = "none"

    fairness_policy = FairnessPolicy(
        avoid_protected_attr_discrimination=avoid_disc,  # type: ignore[arg-type]
        prioritize_worse_off="moderate" if fairness_w >= 0.15 else "mild",  # type: ignore[arg-type]
        use_group_fairness_metrics=["equal_opportunity"],
    )

    vulnerable_policy = VulnerablePriorityPolicy(
        enabled=vuln_w > 0.0,
        priority_strength=vuln_strength,  # type: ignore[arg-type]
        eligible_categories=["children", "elderly", "disabled"],
    )

    # Privacy
    if privacy_w >= 0.25:
        surv = "minimal"
        sharing = "opt_in"
        retention = 7
    elif privacy_w >= 0.15:
        surv = "contextual"
        sharing = "opt_in"
        retention = 30
    else:
        surv = "contextual"
        sharing = "opt_out"
        retention = 90

    privacy_policy = PrivacyPolicy(
        default_surveillance=surv,  # type: ignore[arg-type]
        third_party_data_sharing=sharing,  # type: ignore[arg-type]
        data_retention_days=retention,
    )

    # Environment
    if env_w >= 0.25:
        energy_priority = "high"
    elif env_w >= 0.15:
        energy_priority = "moderate"
    else:
        energy_priority = "low"

    environment_policy = EnvironmentPolicy(
        energy_priority=energy_priority,  # type: ignore[arg-type]
        allow_high_energy_mode=env_w < 0.3,
        require_explanation_for_high_energy=env_w >= 0.15,
    )

    # Rule following: more safety + fairness → more protocol-respecting by default.
    rf_policy = RuleFollowingPolicy(
        follow_official_protocol_by_default=True,
        allow_rule_deviation_for_better_outcomes="rare",  # type: ignore[arg-type]
        deviation_requires_logging=True,
    )

    # Transparency & oversight: pretty conservative defaults.
    transparency_policy = TransparencyPolicy(
        log_decisions="standard",
        explanation_required_for_high_impact=True,
    )

    oversight_policy = OversightPolicy(
        human_in_the_loop_required="high_risk_only",
        escalation_channels=["ethics_board"],
    )

    # Constraints / pattern rules from hard vetoes
    hard_veto_ids = [hid for hid, enabled in hard_veto_flags.items() if enabled]

    pattern_rules: List[PatternRule] = []

    if hard_veto_flags.get("never_intentional_serious_harm", False):
        pattern_rules.append(
            PatternRule(
                id="never_intentional_serious_harm_rule",
                description=(
                    "Forbid options with very high expected serious harm to a person."
                ),
                priority=100,
                applies_in_domains=["*"],
                if_all=[
                    PatternCondition(
                        path="consequences.expected_harm",
                        op=">=",
                        value=0.8,
                    )
                ],
                effect=PatternEffect(
                    verdict="forbid",
                    min_normative_score=0.0,
                    escalation_required=True,
                ),
                tags=["nonmaleficence", "safety"],
            )
        )

    if hard_veto_flags.get("never_discriminate_protected_groups", False):
        pattern_rules.append(
            PatternRule(
                id="no_protected_group_discrimination",
                description=(
                    "Forbid options that discriminate on protected attributes."
                ),
                priority=100,
                applies_in_domains=["*"],
                if_all=[
                    PatternCondition(
                        path="justice_and_fairness.discriminates_on_protected_attr",
                        op="==",
                        value=True,
                    )
                ],
                effect=PatternEffect(
                    verdict="forbid",
                    min_normative_score=0.0,
                    escalation_required=True,
                ),
                tags=["justice", "fairness"],
            )
        )

    if hard_veto_flags.get("never_needless_harm_to_non_human_life", False):
        pattern_rules.append(
            PatternRule(
                id="avoid_needless_harm_to_non_human_life",
                description=(
                    "Forbid options that needlessly harm non-human life when "
                    "a reasonable alternative exists."
                ),
                priority=90,
                applies_in_domains=["domestic", "environmental"],
                if_all=[
                    PatternCondition(
                        path="societal_and_environmental.harms_non_human_life",
                        op="==",
                        value=True,
                    )
                ],
                effect=PatternEffect(
                    verdict="forbid",
                    min_normative_score=0.0,
                    escalation_required=False,
                ),
                tags=["environment", "non_harm"],
            )
        )

    constraints = Constraints(
        hard_vetoes=hard_veto_ids,
        pattern_rules=pattern_rules,
    )

    return {
        "safety_policy": safety_policy,
        "autonomy_policy": autonomy_policy,
        "fairness_policy": fairness_policy,
        "vulnerable_policy": vulnerable_policy,
        "privacy_policy": privacy_policy,
        "environment_policy": environment_policy,
        "rule_following_policy": rf_policy,
        "transparency_policy": transparency_policy,
        "oversight_policy": oversight_policy,
        "constraints": constraints,
    }


def run_dialogue(config: dict) -> DEMEProfileV01:
    # Basic identity and scope
    name, display_name, stakeholder_group, domain_scope = intro(config)

    # Create initial weights from YAML dimensions
    weights = initialize_weights(config)
    ask_high_level_orientation(config, weights)
    ask_pairwise_tradeoffs(config, weights)
    dim_weights = normalize_weights(weights)

    # Hard vetoes + override mode
    hard_veto_flags = ask_hard_vetoes(config)
    override_policy = ask_override_mode(config)

    # Metadata
    provenance = Provenance(
        collection_method="dialogue",
        participant_count=1,  # can be updated by caller if needed
        jurisdiction=[],
        language=config.get("meta", {}).get("language", "en-US"),
    )
    metadata = Metadata(
        name=name,
        display_name=display_name,
        description=ask_free_text(
            "Brief description of this EM profile (what system and context it applies to)."
        ),
        stakeholder_group=stakeholder_group,
        created_at=Metadata.now_iso(),
        updated_at=Metadata.now_iso(),
        provenance=provenance,
    )

    # Principle alignment
    principle_alignment = derive_principle_alignment(dim_weights)

    # Risk attitude: simple neutral default for now (can be expanded with more questions).
    risk_attitude = RiskAttitude(
        overall="balanced",
        harm_vs_benefit_index=0.5,
        epistemic_caution_index=0.5,
    )

    # Policy blocks & constraints from weights + veto answers
    blocks = derive_policy_blocks_from_weights(dim_weights, hard_veto_flags)

    # Optional notes
    notes_prompt = config.get(
        "notes_prompt",
        "If you want to add any clarifying notes, exceptions, or context, write them here.",
    )
    notes = ask_free_text(notes_prompt)

    # Assemble profile
    profile = DEMEProfileV01(
        metadata=metadata,
        domain_scope=domain_scope,
        principle_alignment=principle_alignment,
        dimension_weights=dim_weights,
        risk_attitude=risk_attitude,
        safety_policy=blocks["safety_policy"],  # type: ignore[arg-type]
        autonomy_policy=blocks["autonomy_policy"],  # type: ignore[arg-type]
        fairness_policy=blocks["fairness_policy"],  # type: ignore[arg-type]
        vulnerable_priority_policy=blocks["vulnerable_policy"],  # type: ignore[arg-type]
        privacy_policy=blocks["privacy_policy"],  # type: ignore[arg-type]
        environment_policy=blocks["environment_policy"],  # type: ignore[arg-type]
        rule_following_policy=blocks["rule_following_policy"],  # type: ignore[arg-type]
        transparency_policy=blocks["transparency_policy"],  # type: ignore[arg-type]
        oversight_policy=blocks["oversight_policy"],  # type: ignore[arg-type]
        constraints=blocks["constraints"],  # type: ignore[arg-type]
        override_policy=override_policy,
        scenario_responses={},  # can be filled later if you log per-scenario answers
        notes=notes,
    )

    return profile


# ---------- Main / CLI ----------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Interactive DEME ethics dialogue (v2).\n"
            "Reads a YAML config and produces a DEMEProfileV01 JSON file."
        )
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="ethical_dialogue_questions.yaml",
        help="Path to YAML config file with questions.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="em_profile_v01.json",
        help="Path to write the resulting EM profile JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    profile = run_dialogue(config)

    out = profile.to_dict()
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 72)
    print(f"DEMEProfileV01 written to: {args.output}")
    print("Dimension weights:")
    for dim, w in profile.dimension_weights.items():
        print(f"  {dim:18s}: {w:.3f}")
    print("Override mode:", profile.override_policy.mode)
    print("Hard vetoes:", profile.constraints.hard_vetoes)
    print("=" * 72)


if __name__ == "__main__":
    main()
