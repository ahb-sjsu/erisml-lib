"""
tests/test_json_schema.py - Unit tests for the ethics JSON-schema module.

Covers Issue #135: every exported schema function is tested with at least
one valid object (positive case) and one invalid object (negative case).
"""

import json
import tempfile
from pathlib import Path

import jsonschema

from erisml.ethics.interop.json_schema import (
    export_schemas_to_files,
    get_decision_proof_schema,
    get_ethical_facts_schema,
    get_ethical_judgement_schema,
    get_ethical_judgement_v2_schema,
    get_moral_vector_schema,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def validate(instance, schema):
    """Return None on success; raise jsonschema.ValidationError on failure."""
    jsonschema.validate(instance=instance, schema=schema)


def is_invalid(instance, schema) -> bool:
    """Return True when the instance does NOT satisfy the schema."""
    try:
        jsonschema.validate(instance=instance, schema=schema)
        return False
    except jsonschema.ValidationError:
        return True


# ---------------------------------------------------------------------------
# get_ethical_facts_schema
# ---------------------------------------------------------------------------


class TestEthicalFactsSchema:
    def test_returns_dict_with_required_keys(self):
        schema = get_ethical_facts_schema()
        assert isinstance(schema, dict)
        assert schema["type"] == "object"
        assert "$schema" in schema
        assert "title" in schema
        assert "properties" in schema
        assert "required" in schema

    def test_required_fields_present(self):
        schema = get_ethical_facts_schema()
        required = schema["required"]
        assert "option_id" in required
        assert "consequences" in required
        assert "rights_and_duties" in required
        assert "justice_and_fairness" in required

    def test_valid_minimal_object(self):
        schema = get_ethical_facts_schema()
        valid = {
            "option_id": "opt_1",
            "consequences": {
                "expected_benefit": 0.8,
                "expected_harm": 0.2,
                "urgency": 0.3,
                "affected_count": 5,
            },
            "rights_and_duties": {
                "violates_rights": False,
                "has_valid_consent": True,
                "violates_explicit_rule": False,
                "role_duty_conflict": False,
            },
            "justice_and_fairness": {
                "discriminates_on_protected_attr": False,
                "prioritizes_most_disadvantaged": True,
                "exploits_vulnerable_population": False,
                "exacerbates_power_imbalance": False,
            },
        }
        validate(valid, schema)  # must not raise

    def test_invalid_missing_option_id(self):
        schema = get_ethical_facts_schema()
        bad = {
            "consequences": {
                "expected_benefit": 0.8,
                "expected_harm": 0.2,
                "urgency": 0.3,
                "affected_count": 5,
            },
            "rights_and_duties": {
                "violates_rights": False,
                "has_valid_consent": True,
                "violates_explicit_rule": False,
                "role_duty_conflict": False,
            },
            "justice_and_fairness": {
                "discriminates_on_protected_attr": False,
                "prioritizes_most_disadvantaged": True,
                "exploits_vulnerable_population": False,
                "exacerbates_power_imbalance": False,
            },
        }
        assert is_invalid(bad, schema)

    def test_invalid_harm_out_of_range(self):
        schema = get_ethical_facts_schema()
        bad = {
            "option_id": "opt_bad",
            "consequences": {
                "expected_benefit": 0.8,
                "expected_harm": 1.5,  # exceeds maximum of 1.0
                "urgency": 0.3,
                "affected_count": 5,
            },
            "rights_and_duties": {
                "violates_rights": False,
                "has_valid_consent": True,
                "violates_explicit_rule": False,
                "role_duty_conflict": False,
            },
            "justice_and_fairness": {
                "discriminates_on_protected_attr": False,
                "prioritizes_most_disadvantaged": True,
                "exploits_vulnerable_population": False,
                "exacerbates_power_imbalance": False,
            },
        }
        assert is_invalid(bad, schema)

    def test_invalid_extra_field_rejected(self):
        schema = get_ethical_facts_schema()
        bad = {
            "option_id": "opt_extra",
            "consequences": {
                "expected_benefit": 0.8,
                "expected_harm": 0.2,
                "urgency": 0.3,
                "affected_count": 5,
            },
            "rights_and_duties": {
                "violates_rights": False,
                "has_valid_consent": True,
                "violates_explicit_rule": False,
                "role_duty_conflict": False,
            },
            "justice_and_fairness": {
                "discriminates_on_protected_attr": False,
                "prioritizes_most_disadvantaged": True,
                "exploits_vulnerable_population": False,
                "exacerbates_power_imbalance": False,
            },
            "unexpected_field": "should_fail",  # additionalProperties: False
        }
        assert is_invalid(bad, schema)


# ---------------------------------------------------------------------------
# get_ethical_judgement_schema
# ---------------------------------------------------------------------------


class TestEthicalJudgementSchema:
    def test_returns_dict_with_required_keys(self):
        schema = get_ethical_judgement_schema()
        assert isinstance(schema, dict)
        assert schema["type"] == "object"
        assert "title" in schema
        assert "required" in schema

    def test_verdict_enum_present(self):
        schema = get_ethical_judgement_schema()
        verdict_enum = schema["properties"]["verdict"]["enum"]
        assert "strongly_prefer" in verdict_enum
        assert "forbid" in verdict_enum

    def test_valid_object(self):
        schema = get_ethical_judgement_schema()
        valid = {
            "option_id": "opt_1",
            "em_name": "GenevaBaselineEM",
            "stakeholder": "patient",
            "verdict": "prefer",
            "normative_score": 0.75,
            "reasons": ["No rights violated", "Consent obtained"],
        }
        validate(valid, schema)

    def test_invalid_verdict_value(self):
        schema = get_ethical_judgement_schema()
        bad = {
            "option_id": "opt_1",
            "em_name": "GenevaBaselineEM",
            "stakeholder": "patient",
            "verdict": "maybe",  # not in enum
            "normative_score": 0.75,
            "reasons": [],
        }
        assert is_invalid(bad, schema)

    def test_invalid_score_out_of_range(self):
        schema = get_ethical_judgement_schema()
        bad = {
            "option_id": "opt_1",
            "em_name": "GenevaBaselineEM",
            "stakeholder": "patient",
            "verdict": "prefer",
            "normative_score": 2.0,  # exceeds maximum of 1.0
            "reasons": [],
        }
        assert is_invalid(bad, schema)


# ---------------------------------------------------------------------------
# get_moral_vector_schema
# ---------------------------------------------------------------------------


class TestMoralVectorSchema:
    def test_returns_dict_with_required_keys(self):
        schema = get_moral_vector_schema()
        assert isinstance(schema, dict)
        assert schema["title"] == "MoralVector"
        assert "required" in schema

    def test_required_dimensions_present(self):
        schema = get_moral_vector_schema()
        required = schema["required"]
        for dim in ["physical_harm", "rights_respect", "fairness_equity",
                    "autonomy_respect", "legitimacy_trust", "epistemic_quality"]:
            assert dim in required

    def test_valid_object(self):
        schema = get_moral_vector_schema()
        valid = {
            "physical_harm": 0.1,
            "rights_respect": 0.9,
            "fairness_equity": 0.8,
            "autonomy_respect": 0.7,
            "legitimacy_trust": 0.95,
            "epistemic_quality": 0.6,
        }
        validate(valid, schema)

    def test_invalid_dimension_out_of_range(self):
        schema = get_moral_vector_schema()
        bad = {
            "physical_harm": -0.1,  # below minimum 0.0
            "rights_respect": 0.9,
            "fairness_equity": 0.8,
            "autonomy_respect": 0.7,
            "legitimacy_trust": 0.95,
            "epistemic_quality": 0.6,
        }
        assert is_invalid(bad, schema)

    def test_invalid_missing_required_dimension(self):
        schema = get_moral_vector_schema()
        bad = {
            "physical_harm": 0.1,
            # missing rights_respect and others
        }
        assert is_invalid(bad, schema)


# ---------------------------------------------------------------------------
# get_ethical_judgement_v2_schema
# ---------------------------------------------------------------------------


class TestEthicalJudgementV2Schema:
    def test_returns_dict_with_required_keys(self):
        schema = get_ethical_judgement_v2_schema()
        assert isinstance(schema, dict)
        assert schema["title"] == "EthicalJudgementV2"
        assert "moral_vector" in schema["required"]

    def test_em_tier_range_defined(self):
        schema = get_ethical_judgement_v2_schema()
        tier = schema["properties"]["em_tier"]
        assert tier["minimum"] == 0
        assert tier["maximum"] == 4

    def test_valid_object(self):
        schema = get_ethical_judgement_v2_schema()
        valid = {
            "option_id": "opt_1",
            "em_name": "GenevaBaselineEM",
            "stakeholder": "patient",
            "em_tier": 0,
            "verdict": "strongly_prefer",
            "moral_vector": {
                "physical_harm": 0.0,
                "rights_respect": 1.0,
                "fairness_equity": 0.9,
                "autonomy_respect": 0.8,
                "legitimacy_trust": 1.0,
                "epistemic_quality": 0.7,
            },
        }
        validate(valid, schema)

    def test_invalid_tier_out_of_range(self):
        schema = get_ethical_judgement_v2_schema()
        bad = {
            "option_id": "opt_1",
            "em_name": "GenevaBaselineEM",
            "stakeholder": "patient",
            "em_tier": 99,  # exceeds maximum of 4
            "verdict": "prefer",
            "moral_vector": {
                "physical_harm": 0.0,
                "rights_respect": 1.0,
                "fairness_equity": 0.9,
                "autonomy_respect": 0.8,
                "legitimacy_trust": 1.0,
                "epistemic_quality": 0.7,
            },
        }
        assert is_invalid(bad, schema)


# ---------------------------------------------------------------------------
# get_decision_proof_schema
# ---------------------------------------------------------------------------


class TestDecisionProofSchema:
    def test_returns_dict_with_required_keys(self):
        schema = get_decision_proof_schema()
        assert isinstance(schema, dict)
        assert schema["title"] == "DecisionProof"
        assert "required" in schema

    def test_required_fields_present(self):
        schema = get_decision_proof_schema()
        for field in ["proof_id", "timestamp", "selected_option_id",
                      "ranked_options", "forbidden_options"]:
            assert field in schema["required"]

    def test_valid_minimal_object(self):
        schema = get_decision_proof_schema()
        valid = {
            "proof_id": "123e4567-e89b-12d3-a456-426614174000",
            "timestamp": "2026-09-30T17:00:00Z",
            "selected_option_id": "opt_1",
            "ranked_options": ["opt_1", "opt_2"],
            "forbidden_options": [],
        }
        validate(valid, schema)

    def test_invalid_missing_required_field(self):
        schema = get_decision_proof_schema()
        bad = {
            "proof_id": "123e4567-e89b-12d3-a456-426614174000",
            # missing timestamp, selected_option_id, ranked_options, forbidden_options
        }
        assert is_invalid(bad, schema)


# ---------------------------------------------------------------------------
# export_schemas_to_files
# ---------------------------------------------------------------------------


class TestExportSchemasToFiles:
    def test_creates_both_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            export_schemas_to_files(output_dir)
            assert (output_dir / "ethical_facts.json").exists()
            assert (output_dir / "ethical_judgement.json").exists()

    def test_exported_files_are_valid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            export_schemas_to_files(output_dir)
            for fname in ["ethical_facts.json", "ethical_judgement.json"]:
                content = (output_dir / fname).read_text(encoding="utf-8")
                parsed = json.loads(content)
                assert isinstance(parsed, dict)

    def test_exported_facts_schema_matches_function(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            export_schemas_to_files(output_dir)
            content = (output_dir / "ethical_facts.json").read_text(encoding="utf-8")
            from_file = json.loads(content)
            from_function = get_ethical_facts_schema()
            assert from_file == from_function
