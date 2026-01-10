#!/usr/bin/env python3
"""
hello_deme.py

A production-ready example script for ErisML.
Correctly handles the MCP Server requirement for Dictionary inputs
instead of raw Python objects.
"""

import argparse
import json
import logging
import sys
import dataclasses
from typing import List, Any, Type

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("DEME")

try:
    from erisml.ethics.interop import mcp_deme_server as deme
    from erisml.ethics.facts import (
        EthicalFacts,
        Consequences,
        RightsAndDuties,
        JusticeAndFairness,
    )
except ImportError:
    logger.critical("ErisML library not found. Ensure you are in the repo root.")
    sys.exit(1)


def auto_fill(cls: Type, **overrides) -> Any:
    """
    Dynamically creates a class instance with valid defaults for all fields.
    """
    valid_args = {}
    for field in dataclasses.fields(cls):
        if field.name in overrides:
            valid_args[field.name] = overrides[field.name]
        elif field.default == dataclasses.MISSING:
            if field.type == bool:
                valid_args[field.name] = False
            elif field.type == float:
                valid_args[field.name] = 0.5
            elif field.type == int:
                valid_args[field.name] = 1
            elif field.type == str:
                valid_args[field.name] = "default"
            else:
                valid_args[field.name] = None
    return cls(**valid_args)


def run_governance_simulation(
    profile_id: str, options: List[str], json_output: bool
) -> None:
    print(f"\n🤖 --- DEME Governance Simulation: {profile_id} ---\n")
    logger.info(f"Modelling ethical facts for {len(options)} options...")

    formatted_options = []
    for opt in options:
        is_patient_a = "A" in opt
        try:
            # 1. Create the rich objects using auto-fill logic
            cons = auto_fill(
                Consequences,
                expected_benefit=0.9 if is_patient_a else 0.4,
                expected_harm=0.1 if is_patient_a else 0.6,
                urgency=0.2 if is_patient_a else 0.9,
                affected_count=1,
            )
            rights = auto_fill(RightsAndDuties, role_duty_conflict=False)
            justice = auto_fill(JusticeAndFairness, distributive_pattern="maximin")

            facts_obj = auto_fill(
                EthicalFacts,
                option_id=opt,
                consequences=cons,
                rights_and_duties=rights,
                justice_and_fairness=justice,
            )

            # --- THE FIX IS HERE ---
            # Convert the Python Object back into a Dictionary (JSON)
            # because the MCP server refuses to handle raw Objects.
            facts_dict = dataclasses.asdict(facts_obj)

            formatted_options.append({"option_id": opt, "ethical_facts": facts_dict})

        except Exception as e:
            logger.error(f"Error building data for {opt}: {e}")
            return

    # --- Evaluation ---
    logger.info("Requesting ethical evaluation...")
    try:
        eval_result = deme.evaluate_options(profile_id, formatted_options)
        judgements = eval_result.get("judgements", [])
        logger.info(f"Success! Received {len(judgements)} judgements.")
    except Exception as e:
        logger.error(f"Evaluation Runtime Error: {e}")
        return

    # --- Governance ---
    logger.info("Governing decision...")
    try:
        decision = deme.govern_decision(
            profile_id=profile_id, option_ids=options, judgements=judgements
        )
    except Exception as e:
        logger.error(f"Governance Runtime Error: {e}")
        return

    # --- Output ---
    selected = decision.get("selected_option", "None")
    rationale = decision.get("rationale", "No rationale")

    print("\n📝 --- Result ---")
    print(f"✅ SELECTED ACTION: {selected}")
    print(f"⚖️ RATIONALE:       {rationale}")

    if json_output:
        print("\n🔍 --- Audit Trail ---")
        print(json.dumps(decision, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="hospital_v1")
    parser.add_argument(
        "--options",
        nargs="+",
        default=["allocate_to_patient_A", "allocate_to_patient_B"],
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    run_governance_simulation(args.profile, args.options, args.json)


if __name__ == "__main__":
    main()
