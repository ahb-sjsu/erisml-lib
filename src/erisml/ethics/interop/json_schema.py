"""
JSON Schema definitions for DEME / ethics types.

These schemas are intended for:

- language-agnostic interop (e.g., other services constructing EthicalFacts),
- validation in pipelines or config systems,
- documentation and code generation.

They are **hand-authored** to match the dataclasses in:

- erisml.ethics.facts
- erisml.ethics.judgement
- erisml.ethics.moral_vector (DEME 2.0)

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def _dimension_schemas() -> Dict[str, Dict[str, Any]]:
    """
    Return JSON Schemas for the ethical dimension objects used within
    EthicalFacts.

    This is an internal helper; top-level callers should use
    get_ethical_facts_schema() and get_ethical_judgement_schema().
    """
    consequences = {
        "type": "object",
        "properties": {
            "expected_benefit": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "expected_harm": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "urgency": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "affected_count": {"type": "integer", "minimum": 0},
        },
        "required": [
            "expected_benefit",
            "expected_harm",
            "urgency",
            "affected_count",
        ],
        "additionalProperties": False,
    }

    rights_and_duties = {
        "type": "object",
        "properties": {
            "violates_rights": {"type": "boolean"},
            "has_valid_consent": {"type": "boolean"},
            "violates_explicit_rule": {"type": "boolean"},
            "role_duty_conflict": {"type": "boolean"},
        },
        "required": [
            "violates_rights",
            "has_valid_consent",
            "violates_explicit_rule",
            "role_duty_conflict",
        ],
        "additionalProperties": False,
    }

    justice_and_fairness = {
        "type": "object",
        "properties": {
            "discriminates_on_protected_attr": {"type": "boolean"},
            "prioritizes_most_disadvantaged": {"type": "boolean"},
            "distributive_pattern": {"type": ["string", "null"]},
            "exploits_vulnerable_population": {"type": "boolean"},
            "exacerbates_power_imbalance": {"type": "boolean"},
        },
        "required": [
            "discriminates_on_protected_attr",
            "prioritizes_most_disadvantaged",
            "exploits_vulnerable_population",
            "exacerbates_power_imbalance",
        ],
        "additionalProperties": False,
    }

    autonomy_and_agency = {
        "type": "object",
        "properties": {
            "has_meaningful_choice": {"type": "boolean"},
            "coercion_or_undue_influence": {"type": "boolean"},
            "can_withdraw_without_penalty": {"type": "boolean"},
            "manipulative_design_present": {"type": "boolean"},
        },
        "required": [
            "has_meaningful_choice",
            "coercion_or_undue_influence",
            "can_withdraw_without_penalty",
            "manipulative_design_present",
        ],
        "additionalProperties": False,
    }

    privacy_and_data = {
        "type": "object",
        "properties": {
            "privacy_invasion_level": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "data_minimization_respected": {"type": "boolean"},
            "secondary_use_without_consent": {"type": "boolean"},
            "data_retention_excessive": {"type": "boolean"},
            "reidentification_risk": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
        },
        "required": [
            "privacy_invasion_level",
            "data_minimization_respected",
            "secondary_use_without_consent",
            "data_retention_excessive",
            "reidentification_risk",
        ],
        "additionalProperties": False,
    }

    societal_and_environmental = {
        "type": "object",
        "properties": {
            "environmental_harm": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "long_term_societal_risk": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "benefits_to_future_generations": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "burden_on_vulnerable_groups": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
        },
        "required": [
            "environmental_harm",
            "long_term_societal_risk",
            "benefits_to_future_generations",
            "burden_on_vulnerable_groups",
        ],
        "additionalProperties": False,
    }

    virtue_and_care = {
        "type": "object",
        "properties": {
            "expresses_compassion": {"type": "boolean"},
            "betrays_trust": {"type": "boolean"},
            "respects_person_as_end": {"type": "boolean"},
        },
        "required": [
            "expresses_compassion",
            "betrays_trust",
            "respects_person_as_end",
        ],
        "additionalProperties": False,
    }

    procedural_and_legitimacy = {
        "type": "object",
        "properties": {
            "followed_approved_procedure": {"type": "boolean"},
            "stakeholders_consulted": {"type": "boolean"},
            "decision_explainable_to_public": {"type": "boolean"},
            "contestation_available": {"type": "boolean"},
        },
        "required": [
            "followed_approved_procedure",
            "stakeholders_consulted",
            "decision_explainable_to_public",
            "contestation_available",
        ],
        "additionalProperties": False,
    }

    epistemic_status = {
        "type": "object",
        "properties": {
            "uncertainty_level": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "evidence_quality": {
                "type": "string",
                "enum": ["low", "medium", "high"],
            },
            "novel_situation_flag": {"type": "boolean"},
        },
        "required": [
            "uncertainty_level",
            "evidence_quality",
            "novel_situation_flag",
        ],
        "additionalProperties": False,
    }

    return {
        "Consequences": consequences,
        "RightsAndDuties": rights_and_duties,
        "JusticeAndFairness": justice_and_fairness,
        "AutonomyAndAgency": autonomy_and_agency,
        "PrivacyAndDataGovernance": privacy_and_data,
        "SocietalAndEnvironmental": societal_and_environmental,
        "VirtueAndCare": virtue_and_care,
        "ProceduralAndLegitimacy": procedural_and_legitimacy,
        "EpistemicStatus": epistemic_status,
    }


def get_ethical_facts_schema() -> Dict[str, Any]:
    """
    Return a JSON Schema (draft-07 compatible) for the EthicalFacts object.

    This schema is suitable for validation of JSON payloads used to construct
    EthicalFacts instances, and for documentation / interop.
    """
    dims = _dimension_schemas()

    schema: Dict[str, Any] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://ahb-sjsu.github.io/erisml-lib/schemas/ethical_facts.json",
        "title": "EthicalFacts",
        "type": "object",
        "description": (
            "Ethically relevant facts for a single candidate option. "
            "Constructed by domain and assessment layers, consumed by "
            "ethics-only modules."
        ),
        "properties": {
            "option_id": {"type": "string"},
            "consequences": dims["Consequences"],
            "rights_and_duties": dims["RightsAndDuties"],
            "justice_and_fairness": dims["JusticeAndFairness"],
            "autonomy_and_agency": {
                "anyOf": [
                    dims["AutonomyAndAgency"],
                    {"type": "null"},
                ]
            },
            "privacy_and_data": {
                "anyOf": [
                    dims["PrivacyAndDataGovernance"],
                    {"type": "null"},
                ]
            },
            "societal_and_environmental": {
                "anyOf": [
                    dims["SocietalAndEnvironmental"],
                    {"type": "null"},
                ]
            },
            "virtue_and_care": {
                "anyOf": [
                    dims["VirtueAndCare"],
                    {"type": "null"},
                ]
            },
            "procedural_and_legitimacy": {
                "anyOf": [
                    dims["ProceduralAndLegitimacy"],
                    {"type": "null"},
                ]
            },
            "epistemic_status": {
                "anyOf": [
                    dims["EpistemicStatus"],
                    {"type": "null"},
                ]
            },
            "tags": {
                "type": ["array", "null"],
                "items": {"type": "string"},
            },
            "extra": {
                "type": ["object", "null"],
                "additionalProperties": True,
            },
        },
        "required": [
            "option_id",
            "consequences",
            "rights_and_duties",
            "justice_and_fairness",
        ],
        "additionalProperties": False,
    }
    return schema


def get_ethical_judgement_schema() -> Dict[str, Any]:
    """
    Return a JSON Schema (draft-07 compatible) for the EthicalJudgement object.

    This schema is suitable for validation of JSON payloads used to transport
    EM outputs and governance-level judgements.
    """
    schema: Dict[str, Any] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://ahb-sjsu.github.io/erisml-lib/schemas/ethical_judgement.json",
        "title": "EthicalJudgement",
        "type": "object",
        "description": (
            "Normative assessment of a candidate option by a single ethics "
            "module (EM) or governance layer."
        ),
        "properties": {
            "option_id": {"type": "string"},
            "em_name": {"type": "string"},
            "stakeholder": {"type": "string"},
            "verdict": {
                "type": "string",
                "enum": [
                    "strongly_prefer",
                    "prefer",
                    "neutral",
                    "avoid",
                    "forbid",
                ],
            },
            "normative_score": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "reasons": {
                "type": "array",
                "items": {"type": "string"},
            },
            "metadata": {
                "type": "object",
                "additionalProperties": True,
            },
        },
        "required": [
            "option_id",
            "em_name",
            "stakeholder",
            "verdict",
            "normative_score",
            "reasons",
        ],
        "additionalProperties": False,
    }
    return schema


def export_schemas_to_files(output_dir: Path) -> None:
    """
    Export all JSON schemas to files in the specified directory.

    Args:
        output_dir: Directory where schema files should be written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export ethical_facts schema
    ethical_facts_schema = get_ethical_facts_schema()
    ethical_facts_path = output_dir / "ethical_facts.json"
    with open(ethical_facts_path, "w", encoding="utf-8") as f:
        json.dump(ethical_facts_schema, f, indent=2, ensure_ascii=False)
    print(f"Exported ethical_facts schema to {ethical_facts_path}")

    # Export ethical_judgement schema
    ethical_judgement_schema = get_ethical_judgement_schema()
    ethical_judgement_path = output_dir / "ethical_judgement.json"
    with open(ethical_judgement_path, "w", encoding="utf-8") as f:
        json.dump(ethical_judgement_schema, f, indent=2, ensure_ascii=False)
    print(f"Exported ethical_judgement schema to {ethical_judgement_path}")


# ============================================================================
# DEME 2.0 Schemas
# ============================================================================


def get_moral_vector_schema() -> Dict[str, Any]:
    """
    Return a JSON Schema for the MoralVector type (DEME 2.0).

    MoralVector is a k-dimensional ethical assessment vector with
    values in [0, 1] for each dimension.
    """
    schema: Dict[str, Any] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://ahb-sjsu.github.io/erisml-lib/schemas/moral_vector.json",
        "title": "MoralVector",
        "type": "object",
        "description": (
            "k-dimensional ethical assessment vector (DEME 2.0). "
            "Each dimension is a value in [0, 1]."
        ),
        "properties": {
            "physical_harm": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Level of physical harm (0=none, 1=severe)",
            },
            "rights_respect": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Respect for rights (0=violated, 1=fully respected)",
            },
            "fairness_equity": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Fairness and equity (0=unfair, 1=fully fair)",
            },
            "autonomy_respect": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Respect for autonomy (0=coerced, 1=fully autonomous)",
            },
            "legitimacy_trust": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Legitimacy and trust (0=illegitimate, 1=fully legitimate)",
            },
            "epistemic_quality": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Epistemic quality (0=uncertain, 1=certain)",
            },
            "extensions": {
                "type": "object",
                "additionalProperties": {"type": "number"},
                "description": "Custom extension dimensions",
            },
            "veto_flags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of veto flag codes",
            },
            "reason_codes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of reason codes explaining the assessment",
            },
        },
        "required": [
            "physical_harm",
            "rights_respect",
            "fairness_equity",
            "autonomy_respect",
            "legitimacy_trust",
            "epistemic_quality",
        ],
        "additionalProperties": False,
    }
    return schema


def get_ethical_judgement_v2_schema() -> Dict[str, Any]:
    """
    Return a JSON Schema for the EthicalJudgementV2 type (DEME 2.0).

    EthicalJudgementV2 includes a MoralVector instead of a scalar normative_score.
    """
    moral_vector_ref = {"$ref": "#/definitions/MoralVector"}

    schema: Dict[str, Any] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://ahb-sjsu.github.io/erisml-lib/schemas/ethical_judgement_v2.json",
        "title": "EthicalJudgementV2",
        "type": "object",
        "description": (
            "Normative assessment using MoralVector (DEME 2.0). "
            "Replaces scalar normative_score with k-dimensional vector."
        ),
        "definitions": {
            "MoralVector": get_moral_vector_schema(),
        },
        "properties": {
            "option_id": {"type": "string"},
            "em_name": {"type": "string"},
            "stakeholder": {"type": "string"},
            "em_tier": {
                "type": "integer",
                "minimum": 0,
                "maximum": 4,
                "description": "EM tier (0=Constitutional, 1=Core Safety, 2=Rights/Fairness, 3=Soft Values, 4=Meta)",
            },
            "verdict": {
                "type": "string",
                "enum": [
                    "strongly_prefer",
                    "prefer",
                    "neutral",
                    "avoid",
                    "forbid",
                ],
            },
            "moral_vector": moral_vector_ref,
            "veto_triggered": {"type": "boolean"},
            "veto_reason": {"type": ["string", "null"]},
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "reasons": {
                "type": "array",
                "items": {"type": "string"},
            },
            "metadata": {
                "type": "object",
                "additionalProperties": True,
            },
        },
        "required": [
            "option_id",
            "em_name",
            "stakeholder",
            "em_tier",
            "verdict",
            "moral_vector",
        ],
        "additionalProperties": False,
    }
    return schema


def get_decision_proof_schema() -> Dict[str, Any]:
    """
    Return a JSON Schema for the DecisionProof audit artifact (DEME 2.0).
    """
    schema: Dict[str, Any] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://ahb-sjsu.github.io/erisml-lib/schemas/decision_proof.json",
        "title": "DecisionProof",
        "type": "object",
        "description": (
            "Audit artifact capturing the ethical decision process (DEME 2.0). "
            "Includes hash chain for verification."
        ),
        "properties": {
            "proof_id": {"type": "string", "format": "uuid"},
            "timestamp": {"type": "string", "format": "date-time"},
            "profile_id": {"type": ["string", "null"]},
            "input_facts": {
                "type": "array",
                "items": {"$ref": "ethical_facts.json"},
            },
            "layer_outputs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "layer_name": {"type": "string"},
                        "vetoed_options": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "latency_ms": {"type": "number"},
                    },
                },
            },
            "em_judgements": {
                "type": "array",
                "items": {"$ref": "ethical_judgement_v2.json"},
            },
            "selected_option_id": {"type": ["string", "null"]},
            "ranked_options": {
                "type": "array",
                "items": {"type": "string"},
            },
            "forbidden_options": {
                "type": "array",
                "items": {"type": "string"},
            },
            "moral_vector_summary": {
                "type": "object",
                "additionalProperties": {"$ref": "#/definitions/MoralVector"},
            },
            "previous_proof_hash": {"type": ["string", "null"]},
        },
        "required": [
            "proof_id",
            "timestamp",
            "selected_option_id",
            "ranked_options",
            "forbidden_options",
        ],
        "additionalProperties": False,
    }
    return schema


__all__ = [
    "get_ethical_facts_schema",
    "get_ethical_judgement_schema",
    "get_moral_vector_schema",
    "get_ethical_judgement_v2_schema",
    "get_decision_proof_schema",
    "export_schemas_to_files",
]
