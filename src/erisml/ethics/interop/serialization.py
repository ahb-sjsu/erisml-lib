"""
Serialization helpers for DEME / ethics types.

This module converts between:

- Python dataclasses:
    * EthicalFacts and its dimension objects
    * EthicalJudgement

and

- Plain JSON-serializable dicts (matching json_schema.py).

No external libraries are required; this intentionally keeps the
serialization layer lightweight and embeddable.

Version: 0.2 (EthicalDomains update)
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Optional

from ..facts import (
    EthicalFacts,
    Consequences,
    RightsAndDuties,
    JusticeAndFairness,
    AutonomyAndAgency,
    PrivacyAndDataGovernance,
    SocietalAndEnvironmental,
    VirtueAndCare,
    ProceduralAndLegitimacy,
    EpistemicStatus,
)
from ..judgement import EthicalJudgement


# ---------------------------------------------------------------------------
# EthicalFacts serialization
# ---------------------------------------------------------------------------


def _dataclass_to_dict_or_none(obj: Any) -> Optional[Dict[str, Any]]:
    """
    Convert a dataclass instance to a dict, or propagate None.

    This is a small helper to avoid repeated None checks.
    """
    if obj is None:
        return None
    if not is_dataclass(obj):
        raise TypeError(f"Expected dataclass or None, got {type(obj)!r}")
    return asdict(obj)


def ethical_facts_to_dict(facts: EthicalFacts) -> Dict[str, Any]:
    """
    Convert an EthicalFacts instance into a JSON-serializable dict.

    The resulting structure matches the schema returned by
    get_ethical_facts_schema() in json_schema.py.
    """
    data: Dict[str, Any] = {
        "option_id": facts.option_id,
        "consequences": asdict(facts.consequences),
        "rights_and_duties": asdict(facts.rights_and_duties),
        "justice_and_fairness": asdict(facts.justice_and_fairness),
        "autonomy_and_agency": _dataclass_to_dict_or_none(facts.autonomy_and_agency),
        "privacy_and_data": _dataclass_to_dict_or_none(facts.privacy_and_data),
        "societal_and_environmental": _dataclass_to_dict_or_none(
            facts.societal_and_environmental
        ),
        "virtue_and_care": _dataclass_to_dict_or_none(facts.virtue_and_care),
        "procedural_and_legitimacy": _dataclass_to_dict_or_none(
            facts.procedural_and_legitimacy
        ),
        "epistemic_status": _dataclass_to_dict_or_none(facts.epistemic_status),
        "tags": facts.tags if facts.tags is not None else None,
        "extra": facts.extra if facts.extra is not None else None,
    }
    return data


def _build_optional_dimension(
    cls,
    payload: Any,
    *,
    field_name: str,
) -> Any:
    """
    Build an optional dimension dataclass from a nested dict or None.

    Args:
        cls:
            Dataclass type to construct (e.g., AutonomyAndAgency).

        payload:
            Dict representing the dataclass, or None.

        field_name:
            Human-readable field name for error messages.

    Returns:
        Dataclass instance or None.
    """
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise TypeError(
            f"Expected dict or None for {field_name}, got {type(payload)!r}"
        )
    return cls(**payload)


def ethical_facts_from_dict(data: Dict[str, Any]) -> EthicalFacts:
    """
    Construct an EthicalFacts instance from a dict.

    The input is expected to conform (approximately) to the schema produced by
    get_ethical_facts_schema(). This function performs light structural checks
    and will raise TypeError/KeyError for obviously invalid inputs.

    It does *not* perform full JSON Schema validation.
    """
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict for EthicalFacts, got {type(data)!r}")

    try:
        option_id = data["option_id"]

        consequences_raw = data["consequences"]
        rights_raw = data["rights_and_duties"]
        justice_raw = data["justice_and_fairness"]
    except KeyError as exc:
        raise KeyError(
            f"Missing required field in EthicalFacts: {exc.args[0]!r}"
        ) from exc

    if not isinstance(consequences_raw, dict):
        raise TypeError(
            f"'consequences' must be a dict, got {type(consequences_raw)!r}"
        )
    if not isinstance(rights_raw, dict):
        raise TypeError(f"'rights_and_duties' must be a dict, got {type(rights_raw)!r}")
    if not isinstance(justice_raw, dict):
        raise TypeError(
            f"'justice_and_fairness' must be a dict, got {type(justice_raw)!r}"
        )

    consequences = Consequences(**consequences_raw)
    rights_and_duties = RightsAndDuties(**rights_raw)
    justice_and_fairness = JusticeAndFairness(**justice_raw)

    autonomy = _build_optional_dimension(
        AutonomyAndAgency,
        data.get("autonomy_and_agency"),
        field_name="autonomy_and_agency",
    )
    privacy = _build_optional_dimension(
        PrivacyAndDataGovernance,
        data.get("privacy_and_data"),
        field_name="privacy_and_data",
    )
    societal_env = _build_optional_dimension(
        SocietalAndEnvironmental,
        data.get("societal_and_environmental"),
        field_name="societal_and_environmental",
    )
    virtue = _build_optional_dimension(
        VirtueAndCare,
        data.get("virtue_and_care"),
        field_name="virtue_and_care",
    )
    procedural = _build_optional_dimension(
        ProceduralAndLegitimacy,
        data.get("procedural_and_legitimacy"),
        field_name="procedural_and_legitimacy",
    )
    epistemic = _build_optional_dimension(
        EpistemicStatus,
        data.get("epistemic_status"),
        field_name="epistemic_status",
    )

    tags = data.get("tags")
    if tags is not None and not isinstance(tags, list):
        raise TypeError(f"'tags' must be a list of strings or None, got {type(tags)!r}")

    extra = data.get("extra")
    if extra is not None and not isinstance(extra, dict):
        raise TypeError(f"'extra' must be a dict or None, got {type(extra)!r}")

    return EthicalFacts(
        option_id=str(option_id),
        consequences=consequences,
        rights_and_duties=rights_and_duties,
        justice_and_fairness=justice_and_fairness,
        autonomy_and_agency=autonomy,
        privacy_and_data=privacy,
        societal_and_environmental=societal_env,
        virtue_and_care=virtue,
        procedural_and_legitimacy=procedural,
        epistemic_status=epistemic,
        tags=tags,
        extra=extra,
    )


# ---------------------------------------------------------------------------
# EthicalJudgement serialization
# ---------------------------------------------------------------------------


def ethical_judgement_to_dict(j: EthicalJudgement) -> Dict[str, Any]:
    """
    Convert an EthicalJudgement instance into a JSON-serializable dict.

    The resulting structure matches the schema returned by
    get_ethical_judgement_schema() in json_schema.py.
    """
    data: Dict[str, Any] = {
        "option_id": j.option_id,
        "em_name": j.em_name,
        "stakeholder": j.stakeholder,
        "verdict": j.verdict,
        "normative_score": j.normative_score,
        "reasons": list(j.reasons),
        # SAFEGUARD: use 'or {}' to prevent NoneType error in dict() conversion
        "metadata": dict(j.metadata or {}),
    }
    return data


def ethical_judgement_from_dict(data: Dict[str, Any]) -> EthicalJudgement:
    """
    Construct an EthicalJudgement instance from a dict.

    The input is expected to conform (approximately) to the schema produced by
    get_ethical_judgement_schema(). This function performs light structural
    checks and will raise TypeError/KeyError for obviously invalid inputs.

    It does *not* perform full JSON Schema validation.
    """
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict for EthicalJudgement, got {type(data)!r}")

    try:
        option_id = data["option_id"]
        em_name = data["em_name"]
        stakeholder = data["stakeholder"]
        verdict = data["verdict"]
        normative_score = data["normative_score"]
        reasons = data["reasons"]
    except KeyError as exc:
        raise KeyError(
            f"Missing required field in EthicalJudgement: {exc.args[0]!r}"
        ) from exc

    metadata = data.get("metadata", {})

    if not isinstance(reasons, list):
        raise TypeError(f"'reasons' must be a list of strings, got {type(reasons)!r}")
    if metadata is not None and not isinstance(metadata, dict):
        raise TypeError(f"'metadata' must be a dict or None, got {type(metadata)!r}")

    return EthicalJudgement(
        option_id=str(option_id),
        em_name=str(em_name),
        stakeholder=str(stakeholder),
        verdict=verdict,  # type: ignore[arg-type]  # validated upstream by design
        normative_score=float(normative_score),
        reasons=[str(r) for r in reasons],
        # SAFEGUARD: use 'or {}' to prevent NoneType error
        metadata=dict(metadata or {}),
    )


__all__ = [
    "ethical_facts_to_dict",
    "ethical_facts_from_dict",
    "ethical_judgement_to_dict",
    "ethical_judgement_from_dict",
]