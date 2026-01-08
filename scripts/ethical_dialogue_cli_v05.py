#!/usr/bin/env python
"""
ethical_dialogue_cli_v05.py

Interactive, YAML-driven DEME ethics dialogue that builds a DEMEProfileV04.

DEME 2.0 version with MoralVector-based dimension weights and tiered EM architecture.

New in V05:
  - Generates DEMEProfileV04 with MoralVector dimension weights
  - Configures tiered EM architecture (Tier 0-4)
  - Sets layer configs (reflex, tactical, strategic)
  - Maps dialogue responses to DEME 2.0 constructs
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict
from typing import Any, Dict, List

import yaml  # pip install pyyaml

from erisml.ethics.profile_v04 import (
    DEMEProfileV04,
    EMTierConfig,
    deme_profile_v04_to_dict,
)
from erisml.ethics.governance.config_v2 import DimensionWeights


# ---------------------------------------------------------------------------
# CLI helpers (same as v04)
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
    title = meta_cfg.get("title", "DEME 2.0 Ethics Dialogue")
    desc = meta_cfg.get("description", "")

    print("=" * 72)
    print(f" {title} (DEME 2.0)")
    print("=" * 72)
    if desc:
        print(desc)
        print()

    print(
        "This dialogue configures a DEMEProfileV04 with MoralVector-based\n"
        "dimension weights and tiered EM architecture.\n"
    )

    name = input(
        "Internal name for this EM profile (e.g., 'Medical_Steward_v1'): "
    ).strip()
    if not name:
        name = "EM_Profile_V04"

    stakeholder = ask_free_text(
        "Who does this profile represent? (e.g., 'patients_and_public', "
        "'hospital_ethics_board', 'care_facility')"
    )
    if not stakeholder:
        stakeholder = "unspecified_stakeholder"

    description = ask_free_text(
        "Brief description of this profile (what system/context it applies to):"
    )

    return {
        "name": name,
        "stakeholder": stakeholder,
        "description": description,
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


def ask_tier_config() -> Dict[int, EMTierConfig]:
    """Ask about tiered EM configuration for DEME 2.0."""
    print()
    print("-" * 72)
    print("DEME 2.0 Tiered Ethics Module Configuration\n")
    print(
        "DEME 2.0 organizes Ethics Modules (EMs) into tiers:\n"
        "  Tier 0: Constitutional (Geneva, Human Rights) - always enabled, has veto\n"
        "  Tier 1: Core Safety (physical harm prevention) - enabled by default\n"
        "  Tier 2: Rights/Fairness (autonomy, consent) - enabled by default\n"
        "  Tier 3: Soft Values (beneficence, care) - configurable\n"
        "  Tier 4: Meta-Governance (pattern detection) - configurable\n"
    )

    tier_configs: Dict[int, EMTierConfig] = {}

    # Tier 0 - Constitutional (always on, always veto)
    tier_configs[0] = EMTierConfig(
        enabled=True,
        weight=1.0,
        veto_enabled=True,
    )

    # Tier 1 - Core Safety
    tier_configs[1] = EMTierConfig(
        enabled=True,
        weight=0.9,
        veto_enabled=True,
    )

    # Tier 2 - Rights/Fairness
    print("\nTier 2 - Rights & Fairness EMs:")
    idx = ask_choice(
        "How strongly should rights/fairness considerations weigh?",
        [
            "Very strongly (1.0 weight, can veto)",
            "Strongly (0.8 weight, can veto)",
            "Moderately (0.6 weight, advisory only)",
            "Lightly (0.4 weight, advisory only)",
        ],
    )
    weights = [1.0, 0.8, 0.6, 0.4]
    vetos = [True, True, False, False]
    tier_configs[2] = EMTierConfig(
        enabled=True,
        weight=weights[idx],
        veto_enabled=vetos[idx],
    )

    # Tier 3 - Soft Values
    print("\nTier 3 - Soft Values (beneficence, care, virtue):")
    idx = ask_choice(
        "How should soft value EMs influence decisions?",
        [
            "Enable with moderate weight (0.5)",
            "Enable with light weight (0.3)",
            "Disable (focus only on hard constraints)",
        ],
    )
    if idx == 2:
        tier_configs[3] = EMTierConfig(enabled=False, weight=0.0, veto_enabled=False)
    else:
        weights = [0.5, 0.3]
        tier_configs[3] = EMTierConfig(
            enabled=True,
            weight=weights[idx],
            veto_enabled=False,
        )

    # Tier 4 - Meta-Governance
    print("\nTier 4 - Meta-Governance (pattern detection, gaming prevention):")
    enable_meta = ask_yes_no(
        "Enable meta-governance EMs to detect manipulation patterns?", default=True
    )
    tier_configs[4] = EMTierConfig(
        enabled=enable_meta,
        weight=0.3 if enable_meta else 0.0,
        veto_enabled=False,
    )

    return tier_configs


def ask_layer_config() -> Dict[str, bool]:
    """Ask about three-layer architecture configuration."""
    print()
    print("-" * 72)
    print("DEME 2.0 Three-Layer Architecture\n")
    print(
        "DEME 2.0 uses a three-layer processing pipeline:\n"
        "  Reflex Layer: Fast veto checks for clear violations (<100 microseconds)\n"
        "  Tactical Layer: Full MoralVector reasoning (10-100 milliseconds)\n"
        "  Strategic Layer: Policy optimization (for future use)\n"
    )

    layer_config: Dict[str, bool] = {}

    layer_config["reflex_enabled"] = ask_yes_no(
        "Enable Reflex Layer for fast veto checks?", default=True
    )

    layer_config["tactical_enabled"] = ask_yes_no(
        "Enable Tactical Layer for full MoralVector reasoning?", default=True
    )

    layer_config["strategic_enabled"] = ask_yes_no(
        "Enable Strategic Layer for policy optimization? (experimental)", default=False
    )

    return layer_config


# ---------------------------------------------------------------------------
# Derivation helpers - Map to DEME 2.0 MoralVector dimensions
# ---------------------------------------------------------------------------


def derive_moral_dimension_weights(
    norm_scores: Dict[str, float], hv_flags: Dict[str, bool]
) -> DimensionWeights:
    """
    Map dialogue dimension scores to MoralVector DimensionWeights.

    MoralVector dimensions:
      - physical_harm (higher = more harm is tolerated before rejection)
      - rights_respect
      - fairness_equity
      - autonomy_respect
      - legitimacy_trust
      - epistemic_quality
    """
    # Base weights from dialogue
    safety = norm_scores.get("safety", 0.15)
    autonomy = norm_scores.get("autonomy", 0.15)
    fairness = norm_scores.get("fairness", 0.15)
    privacy = norm_scores.get("privacy", 0.1)
    rule_following = norm_scores.get("rule_following", 0.1)
    vulnerable_priority = norm_scores.get("vulnerable_priority", 0.1)

    # Map to MoralVector dimensions
    # physical_harm weight: higher safety priority = lower tolerance for harm
    # We invert here since physical_harm in MoralVector is "how much harm"
    physical_harm_weight = 1.0 + safety  # Higher weight = more scrutiny on harm

    rights_respect = 1.0 + autonomy + 0.5 * privacy
    fairness_equity = 1.0 + fairness + 0.5 * vulnerable_priority
    autonomy_respect = 1.0 + autonomy + 0.3 * privacy
    legitimacy_trust = 1.0 + rule_following
    epistemic_quality = 0.5  # Base value, can be adjusted

    # Apply hard veto modifiers
    if hv_flags.get("never_catastrophic_safety_harm", True):
        physical_harm_weight *= 1.5

    if hv_flags.get("never_discriminate_protected_groups", True):
        fairness_equity *= 1.3

    if hv_flags.get("never_violate_explicit_consent_low_stakes", True):
        autonomy_respect *= 1.2

    return DimensionWeights(
        physical_harm=physical_harm_weight,
        rights_respect=rights_respect,
        fairness_equity=fairness_equity,
        autonomy_respect=autonomy_respect,
        legitimacy_trust=legitimacy_trust,
        epistemic_quality=epistemic_quality,
    )


# ---------------------------------------------------------------------------
# Main dialogue flow
# ---------------------------------------------------------------------------


def run_dialogue(config: Dict[str, Any]) -> DEMEProfileV04:
    ident = intro(config)

    scores = initialize_dimension_scores(config)
    ask_high_level(config, scores)
    ask_pairwise(config, scores)
    norm_scores = normalize(scores)

    hv_flags = ask_hard_vetoes(config)
    tier_configs = ask_tier_config()
    layer_config = ask_layer_config()

    moral_dimension_weights = derive_moral_dimension_weights(norm_scores, hv_flags)

    notes_prompt = config.get("notes_prompt", "Any additional notes?")
    notes = ask_free_text(notes_prompt)

    profile = DEMEProfileV04(
        name=ident["name"],
        description=ident["description"],
        stakeholder_label=ident["stakeholder"],
        moral_dimension_weights=moral_dimension_weights,
        tier_configs=tier_configs,
        layer_config=layer_config,
        notes=notes if notes else None,
    )

    return profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interactive DEME 2.0 ethics dialogue (V05 -> DEMEProfileV04 JSON)."
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
        default="em_profile_v04.json",
        help=(
            "Path to write resulting profile JSON. If left as the default "
            "value, a name will be derived from the internal EM profile name, "
            "e.g. 'Medical_Steward_v1.deme_profile_v04.json'."
        ),
    )
    return parser.parse_args()


def derive_output_path(requested_output: str, profile_name: str) -> str:
    """
    If the user left --output at its default value, derive a filename
    from the internal profile name; otherwise, honor the explicit path.
    """
    if requested_output != "em_profile_v04.json":
        return requested_output

    base = profile_name or "EM_Profile_V04"
    # Make it filesystem-friendly: letters, digits, underscore, dash, dot
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", base).strip("_")
    if not safe:
        safe = "EM_Profile_V04"
    return f"{safe}.deme_profile_v04.json"


def main() -> None:
    args = parse_args()
    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    profile = run_dialogue(config)
    data = deme_profile_v04_to_dict(profile)

    output_path = derive_output_path(args.output, profile.name)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 72)
    print(f"DEMEProfileV04 (DEME 2.0) written to: {output_path}")
    print()
    print("MoralVector dimension weights:")
    for k, v in asdict(profile.moral_dimension_weights).items():
        print(f"  {k:20s}: {v:.3f}")
    print()
    print("Tier configurations:")
    for tier_num, tier_cfg in sorted(profile.tier_configs.items()):
        status = "enabled" if tier_cfg.enabled else "disabled"
        veto = "veto" if tier_cfg.veto_enabled else "advisory"
        print(f"  Tier {tier_num}: {status}, weight={tier_cfg.weight:.2f}, {veto}")
    print()
    print("Layer configuration:")
    for layer, enabled in profile.layer_config.items():
        status = "enabled" if enabled else "disabled"
        print(f"  {layer}: {status}")
    print("=" * 72)


if __name__ == "__main__":
    main()
