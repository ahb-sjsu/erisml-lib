"""
erisml.ethics.interop.mcp_deme_server

MCP server exposing DEME as tools, supporting both V1 and V2 architectures:

  V1 Tools (legacy):
  - list_profiles
  - evaluate_options
  - govern_decision

  V2 Tools (DEME 2.0):
  - list_profiles_v2
  - evaluate_options_v2 (returns MoralVectors)
  - govern_decision_v2 (uses MoralVector aggregation)
  - run_pipeline (full three-layer evaluation)

Assumptions:
  - DEME profiles (DEMEProfileV03/V04 JSON) live in a directory
    pointed to by DEME_PROFILES_DIR, or ./deme_profiles by default.
  - V04 profiles are auto-detected by version field.

Version: 2.0.0 (DEME 2.0)
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP  # pip install mcp

# V1 imports (backward compatible)
from erisml.ethics import EthicalJudgement
from erisml.ethics.facts import EthicalFacts
from erisml.ethics.governance.aggregation import (
    DecisionOutcome,
    select_option,
)
from erisml.ethics.interop.profile_adapters import (
    build_triage_ems_and_governance,
)
from erisml.ethics.interop.serialization import (
    ethical_facts_from_dict,
    ethical_judgement_to_dict,
)
from erisml.ethics.profile_v03 import (
    DEMEProfileV03,
    deme_profile_v03_from_dict,
)
from erisml.ethics.modules import EM_REGISTRY

# V2 imports (DEME 2.0)
from erisml.ethics.moral_vector import MoralVector
from erisml.ethics.moral_landscape import MoralLandscape
from erisml.ethics.judgement import EthicalJudgementV2
from erisml.ethics.profile_v04 import DEMEProfileV04, deme_profile_v04_from_dict
from erisml.ethics.profile_migration import migrate_v03_to_v04
from erisml.ethics.governance.config_v2 import GovernanceConfigV2
from erisml.ethics.governance.aggregation_v2 import (
    DecisionOutcomeV2,
    select_option_v2,
)
from erisml.ethics.layers.pipeline import DEMEPipeline, PipelineConfig
from erisml.ethics.modules.registry import EMRegistry


# ---------------------------------------------------------------------------
# MCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP("ErisML DEME Ethics Server")


# ---------------------------------------------------------------------------
# Profile loading & caching (supports both V03 and V04)
# ---------------------------------------------------------------------------

_DEME_PROFILE_CACHE_V03: Dict[str, DEMEProfileV03] = {}
_DEME_PROFILE_CACHE_V04: Dict[str, DEMEProfileV04] = {}
_DEME_PROFILE_DIR: Path = Path(os.environ.get("DEME_PROFILES_DIR", "./deme_profiles"))


def _set_profile_dir(path: Path) -> None:
    """Set the profile directory and clear cache."""
    global _DEME_PROFILE_DIR
    _DEME_PROFILE_DIR = path
    _DEME_PROFILE_CACHE_V03.clear()
    _DEME_PROFILE_CACHE_V04.clear()


def _detect_profile_version(data: Dict[str, Any]) -> str:
    """Detect profile version from JSON data."""
    version = data.get("version", "0.3")
    if version.startswith("0.4"):
        return "v04"
    return "v03"


def _load_profile(profile_id: str) -> DEMEProfileV03:
    """
    Load a V03 profile (legacy support).

    - profile_id is expected to match `${profile_id}.json` in DEME_PROFILES_DIR.
    - V04 profiles are automatically migrated down to V03 for compatibility.
    """
    if profile_id in _DEME_PROFILE_CACHE_V03:
        return _DEME_PROFILE_CACHE_V03[profile_id]

    path = _DEME_PROFILE_DIR / f"{profile_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"DEME profile '{profile_id}' not found at {path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    if _detect_profile_version(data) == "v04":
        # Load as V04 and extract V03 compatibility
        profile_v04 = deme_profile_v04_from_dict(data)
        # For backward compat, create a minimal V03 wrapper
        profile = DEMEProfileV03(
            name=profile_v04.name,
            description=profile_v04.description,
            stakeholder_label=profile_v04.stakeholder_label,
            domain=profile_v04.domain,
            tags=profile_v04.tags,
        )
    else:
        profile = deme_profile_v03_from_dict(data)

    _DEME_PROFILE_CACHE_V03[profile_id] = profile
    return profile


def _load_profile_v04(profile_id: str) -> DEMEProfileV04:
    """
    Load a V04 profile (DEME 2.0).

    - V03 profiles are automatically migrated to V04.
    """
    if profile_id in _DEME_PROFILE_CACHE_V04:
        return _DEME_PROFILE_CACHE_V04[profile_id]

    path = _DEME_PROFILE_DIR / f"{profile_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"DEME profile '{profile_id}' not found at {path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    if _detect_profile_version(data) == "v04":
        profile = deme_profile_v04_from_dict(data)
    else:
        # Migrate V03 to V04
        profile_v03 = deme_profile_v03_from_dict(data)
        profile = migrate_v03_to_v04(profile_v03)

    _DEME_PROFILE_CACHE_V04[profile_id] = profile
    return profile


def _list_profile_files() -> List[Path]:
    if not _DEME_PROFILE_DIR.exists():
        return []
    return sorted(p for p in _DEME_PROFILE_DIR.glob("*.json") if p.is_file())


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_profiles() -> List[Dict[str, Any]]:
    """
    List available DEME profiles known to this server.

    Returns:
      - list of {profile_id, path, name, stakeholder_label, domain,
                 override_mode, tags}
    """
    profiles: List[Dict[str, Any]] = []
    for path in _list_profile_files():
        profile_id = path.stem
        try:
            profile = _load_profile(profile_id)
        except Exception:
            # don't crash the whole tool on one bad profile
            continue

        profiles.append(
            {
                "profile_id": profile_id,
                "path": str(path),
                "name": profile.name,
                "stakeholder_label": profile.stakeholder_label,
                "domain": profile.domain,
                "override_mode": profile.override_mode.value,
                "tags": profile.tags,
                # Optionally expose foundational EMs as metadata
                "base_em_ids": profile.base_em_ids,
                "base_em_enforcement": profile.base_em_enforcement.value,
            }
        )
    return profiles


@mcp.tool()
def evaluate_options(
    profile_id: str,
    options: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Evaluate candidate options ethically using DEME EMs.

    Args:
      profile_id:
        ID of the DEMEProfileV03 JSON file (without .json suffix).
      options:
        List of objects:
          {
            "option_id": "allocate_to_patient_A",
            "ethical_facts": { ... EthicalFacts JSON ... }
          }

    Returns:
      {
        "judgements": [EthicalJudgement JSON ...]
      }
    """
    profile = _load_profile(profile_id)

    # For now we use the triage EMs as our reference EM set.
    # In a production system you'd pick EMs based on profile.domain, tags, etc.
    triage_em, rights_em, gov_cfg = build_triage_ems_and_governance(profile)

    # Start with the two demo EMs.
    ems: Dict[str, Any] = {
        "case_study_1_triage": triage_em,
        "rights_first_compliance": rights_em,
    }

    # Ensure foundational / base EMs are also instantiated and included.
    # These are the "Geneva convention" roots from the profile/governance config.
    for em_id in getattr(gov_cfg, "base_em_ids", []):
        if em_id not in ems:
            em_cls = EM_REGISTRY.get(em_id)
            if em_cls is not None:
                ems[em_id] = em_cls()

    judgements: List[EthicalJudgement] = []

    for opt in options:
        option_id = opt["option_id"]
        ef_dict = opt["ethical_facts"]
        facts: EthicalFacts = ethical_facts_from_dict(ef_dict)

        # Sanity: ensure option IDs match
        if facts.option_id != option_id:
            # you could raise or just overwrite; here we overwrite
            facts.option_id = option_id

        # Run all configured EMs, including foundational/base EMs.
        for em_name, em in ems.items():
            j = em.judge(facts)
            # Ensure em_name is set consistently (helpful for governance logs).
            if j.em_name is None or j.em_name == "":
                j.em_name = em_name
            judgements.append(j)

    return {"judgements": [ethical_judgement_to_dict(j) for j in judgements]}


@mcp.tool()
def govern_decision(
    profile_id: str,
    option_ids: List[str],
    judgements: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Apply DEME governance to a set of EM judgements.

    Args:
      profile_id:
        ID of the DEME profile to use for governance configuration.
      option_ids:
        List of candidate option IDs (must match those in judgements).
      judgements:
        List of EthicalJudgement JSON dicts.

    Returns:
      {
        "selected_option": "option_id or null",
        "forbidden_options": [...],
        "rationale": "...",
        "decision_outcome": { ... JSON-ified DecisionOutcome ... }
      }
    """
    profile = _load_profile(profile_id)
    _, _, gov_cfg = build_triage_ems_and_governance(profile)

    # Group judgements by option_id
    from erisml.ethics.judgement import EthicalJudgement as EJ

    by_option: Dict[str, List[EthicalJudgement]] = {oid: [] for oid in option_ids}

    for jdict in judgements:
        ej = EJ(
            option_id=jdict["option_id"],
            em_name=jdict["em_name"],
            stakeholder=jdict["stakeholder"],
            verdict=jdict["verdict"],
            normative_score=jdict["normative_score"],
            reasons=jdict.get("reasons", []),
            metadata=jdict.get("metadata", {}),
        )
        if ej.option_id in by_option:
            by_option[ej.option_id].append(ej)

    # Use the governance aggregation layer directly.
    decision: DecisionOutcome = select_option(
        by_option,
        gov_cfg,
        candidate_ids=option_ids,
        baseline_option_id=None,
    )

    selected = decision.selected_option_id
    forbidden_options = decision.forbidden_options

    # Build a JSON-friendly DecisionOutcome.
    def _decision_outcome_to_dict(dec: DecisionOutcome) -> Dict[str, Any]:
        return {
            "selected_option_id": dec.selected_option_id,
            "ranked_options": dec.ranked_options,
            "forbidden_options": dec.forbidden_options,
            "rationale": dec.rationale,
            "aggregated_judgements": {
                oid: ethical_judgement_to_dict(j)
                for oid, j in dec.aggregated_judgements.items()
            },
        }

    decision_outcome_json = _decision_outcome_to_dict(decision)

    # Human-readable top-level rationale
    if selected is None:
        rationale = (
            "No permissible option found. "
            f"Forbidden options: {sorted(set(forbidden_options))}."
        )
    else:
        rationale = (
            f"Selected option '{selected}' based on DEME governance "
            f"with profile '{profile_id}' "
            f"(override_mode={profile.override_mode.value}, "
            f"base_em_ids={gov_cfg.base_em_ids})."
        )

    return {
        "selected_option": selected,
        "forbidden_options": sorted(set(forbidden_options)),
        "rationale": rationale,
        "decision_outcome": decision_outcome_json,
    }


# ---------------------------------------------------------------------------
# V2 Tools (DEME 2.0)
# ---------------------------------------------------------------------------


def _moral_vector_to_dict(vec: MoralVector) -> Dict[str, Any]:
    """Convert MoralVector to JSON-serializable dict."""
    return {
        "physical_harm": vec.physical_harm,
        "rights_respect": vec.rights_respect,
        "fairness_equity": vec.fairness_equity,
        "autonomy_respect": vec.autonomy_respect,
        "legitimacy_trust": vec.legitimacy_trust,
        "epistemic_quality": vec.epistemic_quality,
        "extensions": vec.extensions,
        "veto_flags": vec.veto_flags,
        "reason_codes": vec.reason_codes,
    }


def _judgement_v2_to_dict(j: EthicalJudgementV2) -> Dict[str, Any]:
    """Convert EthicalJudgementV2 to JSON-serializable dict."""
    return {
        "option_id": j.option_id,
        "em_name": j.em_name,
        "stakeholder": j.stakeholder,
        "em_tier": j.em_tier,
        "verdict": j.verdict,
        "moral_vector": _moral_vector_to_dict(j.moral_vector),
        "veto_triggered": j.veto_triggered,
        "veto_reason": j.veto_reason,
        "confidence": j.confidence,
        "reasons": j.reasons,
        "metadata": j.metadata,
    }


@mcp.tool()
def list_profiles_v2() -> List[Dict[str, Any]]:
    """
    List available DEME profiles with V2 metadata (DEME 2.0).

    Returns profiles with tier configurations and MoralVector dimension weights.
    """
    profiles: List[Dict[str, Any]] = []
    for path in _list_profile_files():
        profile_id = path.stem
        try:
            profile = _load_profile_v04(profile_id)
        except Exception:
            continue

        profiles.append(
            {
                "profile_id": profile_id,
                "path": str(path),
                "version": "0.4",
                "name": profile.name,
                "description": profile.description,
                "stakeholder_label": profile.stakeholder_label,
                "domain": profile.domain,
                "tags": profile.tags,
                "tier_configs": {
                    str(k): {
                        "enabled": v.enabled,
                        "weight": v.weight,
                        "veto_enabled": v.veto_enabled,
                    }
                    for k, v in profile.tier_configs.items()
                },
                "moral_dimension_weights": {
                    "physical_harm": profile.moral_dimension_weights.physical_harm,
                    "rights_respect": profile.moral_dimension_weights.rights_respect,
                    "fairness_equity": profile.moral_dimension_weights.fairness_equity,
                    "autonomy_respect": profile.moral_dimension_weights.autonomy_respect,
                    "legitimacy_trust": profile.moral_dimension_weights.legitimacy_trust,
                    "epistemic_quality": profile.moral_dimension_weights.epistemic_quality,
                },
            }
        )
    return profiles


@mcp.tool()
def evaluate_options_v2(
    profile_id: str,
    options: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Evaluate candidate options using DEME 2.0 MoralVector-based reasoning.

    Args:
      profile_id:
        ID of the DEME profile (V03 or V04).
      options:
        List of objects:
          {
            "option_id": "option_A",
            "ethical_facts": { ... EthicalFacts JSON ... }
          }

    Returns:
      {
        "judgements": [EthicalJudgementV2 JSON ...],
        "moral_landscape": {option_id: MoralVector, ...}
      }
    """
    profile = _load_profile_v04(profile_id)

    # Build V2 EMs from registry based on tier config

    judgements: List[EthicalJudgementV2] = []
    landscape = MoralLandscape()

    for opt in options:
        option_id = opt["option_id"]
        ef_dict = opt["ethical_facts"]
        facts: EthicalFacts = ethical_facts_from_dict(ef_dict)
        facts.option_id = option_id

        # Get base MoralVector from facts
        base_vector = MoralVector.from_ethical_facts(facts)

        # Run through registered V2 EMs
        for em_id, em_info in EMRegistry.list_all().items():
            tier = em_info.get("tier", 3)
            tier_config = profile.tier_configs.get(tier)

            if tier_config and not tier_config.enabled:
                continue

            em_cls = EMRegistry.get(em_id)
            if em_cls is None:
                continue

            try:
                em = em_cls()
                if hasattr(em, "judge"):
                    j = em.judge(facts)
                    # Convert V1 to V2 if needed
                    if isinstance(j, EthicalJudgement):
                        from erisml.ethics.judgement import judgement_v1_to_v2

                        j = judgement_v1_to_v2(j)
                    judgements.append(j)
            except Exception:
                # Skip failing EMs
                pass

        landscape.add(option_id, base_vector)

    return {
        "judgements": [_judgement_v2_to_dict(j) for j in judgements],
        "moral_landscape": {
            oid: _moral_vector_to_dict(vec) for oid, vec in landscape.vectors.items()
        },
    }


@mcp.tool()
def govern_decision_v2(
    profile_id: str,
    option_ids: List[str],
    judgements: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Apply DEME 2.0 governance with MoralVector aggregation.

    Args:
      profile_id:
        ID of the DEME profile.
      option_ids:
        List of candidate option IDs.
      judgements:
        List of EthicalJudgementV2 JSON dicts.

    Returns:
      {
        "selected_option": "option_id or null",
        "ranked_options": [...],
        "forbidden_options": [...],
        "moral_landscape": {option_id: aggregated_vector, ...},
        "rationale": "...",
      }
    """
    profile = _load_profile_v04(profile_id)

    # Build governance config from profile
    gov_config = GovernanceConfigV2(
        dimension_weights=profile.moral_dimension_weights,
    )

    # Reconstruct judgements
    by_option: Dict[str, List[EthicalJudgementV2]] = {oid: [] for oid in option_ids}

    for jdict in judgements:
        vec = MoralVector(
            physical_harm=jdict["moral_vector"]["physical_harm"],
            rights_respect=jdict["moral_vector"]["rights_respect"],
            fairness_equity=jdict["moral_vector"]["fairness_equity"],
            autonomy_respect=jdict["moral_vector"]["autonomy_respect"],
            legitimacy_trust=jdict["moral_vector"]["legitimacy_trust"],
            epistemic_quality=jdict["moral_vector"]["epistemic_quality"],
            veto_flags=jdict["moral_vector"].get("veto_flags", []),
            reason_codes=jdict["moral_vector"].get("reason_codes", []),
        )

        j = EthicalJudgementV2(
            option_id=jdict["option_id"],
            em_name=jdict["em_name"],
            stakeholder=jdict["stakeholder"],
            em_tier=jdict["em_tier"],
            verdict=jdict["verdict"],
            moral_vector=vec,
            veto_triggered=jdict.get("veto_triggered", False),
            veto_reason=jdict.get("veto_reason"),
            confidence=jdict.get("confidence", 1.0),
            reasons=jdict.get("reasons", []),
            metadata=jdict.get("metadata", {}),
        )

        if j.option_id in by_option:
            by_option[j.option_id].append(j)

    # Run V2 governance
    decision: DecisionOutcomeV2 = select_option_v2(
        by_option,
        gov_config,
        candidate_ids=option_ids,
    )

    return {
        "selected_option": decision.selected_option_id,
        "ranked_options": decision.ranked_options,
        "forbidden_options": decision.forbidden_options,
        "moral_landscape": {
            oid: _moral_vector_to_dict(vec)
            for oid, vec in decision.aggregated_vectors.items()
        },
        "rationale": decision.rationale,
    }


@mcp.tool()
def run_pipeline(
    profile_id: str,
    options: List[Dict[str, Any]],
    include_proof: bool = False,
) -> Dict[str, Any]:
    """
    Run the full DEME 2.0 three-layer pipeline (reflex → tactical → strategic).

    This is the recommended entry point for DEME 2.0 ethical evaluation.

    Args:
      profile_id:
        ID of the DEME profile.
      options:
        List of {option_id, ethical_facts} objects.
      include_proof:
        If True, include full DecisionProof for audit trail.

    Returns:
      {
        "selected_option": "option_id or null",
        "ranked_options": [...],
        "forbidden_options": [...],
        "layer_results": {
          "reflex": {...},
          "tactical": {...},
        },
        "proof": {...} (if include_proof=True)
      }
    """
    profile = _load_profile_v04(profile_id)

    # Build pipeline from profile
    pipeline_config = PipelineConfig(
        reflex_enabled=profile.layer_config.get("reflex_enabled", True),
        tactical_enabled=profile.layer_config.get("tactical_enabled", True),
        strategic_enabled=profile.layer_config.get("strategic_enabled", False),
    )

    pipeline = DEMEPipeline(config=pipeline_config)

    # Prepare facts
    facts_list: List[EthicalFacts] = []
    for opt in options:
        facts = ethical_facts_from_dict(opt["ethical_facts"])
        facts.option_id = opt["option_id"]
        facts_list.append(facts)

    # Run pipeline
    result = pipeline.evaluate(facts_list)

    response: Dict[str, Any] = {
        "selected_option": result.selected_option_id,
        "ranked_options": result.ranked_options,
        "forbidden_options": result.forbidden_options,
        "layer_results": {
            "reflex": {
                "vetoed_options": result.reflex_vetoed,
                "latency_ms": result.reflex_latency_ms,
            },
            "tactical": {
                "moral_landscape": (
                    {
                        oid: _moral_vector_to_dict(vec)
                        for oid, vec in result.tactical_landscape.vectors.items()
                    }
                    if result.tactical_landscape
                    else {}
                ),
                "latency_ms": result.tactical_latency_ms,
            },
        },
    }

    if include_proof and result.proof:
        response["proof"] = {
            "proof_id": result.proof.proof_id,
            "timestamp": result.proof.timestamp.isoformat(),
            "selected_option_id": result.proof.selected_option_id,
            "ranked_options": result.proof.ranked_options,
            "forbidden_options": result.proof.forbidden_options,
            "hash": result.proof.compute_hash(),
        }

    return response


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Main entry point for the ErisML DEME MCP server.

    This function parses command-line arguments and starts the MCP server.
    The server communicates over stdio by default, making it compatible
    with MCP clients like Claude Desktop.
    """
    # Handle --help early to avoid MCP tool registration issues during import
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        # Create parser just for help
        parser = argparse.ArgumentParser(
            description=(
                "ErisML DEME Ethics Server - MCP server exposing DEME (Democratically "
                "Governed Ethics Modules) as tools for ethical decision-making.\n\n"
                "V1 Tools (legacy):\n"
                "  - list_profiles: List available DEME profiles\n"
                "  - evaluate_options: Evaluate options using V1 EMs\n"
                "  - govern_decision: Apply V1 governance\n\n"
                "V2 Tools (DEME 2.0):\n"
                "  - list_profiles_v2: List profiles with MoralVector metadata\n"
                "  - evaluate_options_v2: MoralVector-based evaluation\n"
                "  - govern_decision_v2: MoralVector aggregation governance\n"
                "  - run_pipeline: Full three-layer pipeline (recommended)\n\n"
                "The server communicates over stdio, making it compatible with MCP clients "
                "like Claude Desktop."
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        parser.add_argument(
            "--profiles-dir",
            type=Path,
            default=None,
            help=(
                "Directory containing DEME profile JSON files. "
                "Defaults to ./deme_profiles or DEME_PROFILES_DIR environment variable."
            ),
        )
        parser.add_argument(
            "--log-level",
            type=str,
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default="INFO",
            help="Set the logging level (default: INFO)",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=None,
            help=(
                "Port for HTTP/SSE transport (not yet implemented, server uses stdio by default). "
                "This option is reserved for future use."
            ),
        )
        parser.print_help()
        return

    parser = argparse.ArgumentParser(
        description=(
            "ErisML DEME Ethics Server - MCP server exposing DEME (Democratically "
            "Governed Ethics Modules) as tools for ethical decision-making.\n\n"
            "V1 Tools (legacy):\n"
            "  - list_profiles: List available DEME profiles\n"
            "  - evaluate_options: Evaluate options using V1 EMs\n"
            "  - govern_decision: Apply V1 governance\n\n"
            "V2 Tools (DEME 2.0):\n"
            "  - list_profiles_v2: List profiles with MoralVector metadata\n"
            "  - evaluate_options_v2: MoralVector-based evaluation\n"
            "  - govern_decision_v2: MoralVector aggregation governance\n"
            "  - run_pipeline: Full three-layer pipeline (recommended)\n\n"
            "The server communicates over stdio, making it compatible with MCP clients "
            "like Claude Desktop."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Use default profiles directory (./deme_profiles)\n"
            "  erisml-mcp-server\n\n"
            "  # Specify custom profiles directory\n"
            "  erisml-mcp-server --profiles-dir /path/to/profiles\n\n"
            "  # Set log level to DEBUG\n"
            "  erisml-mcp-server --log-level DEBUG\n\n"
            "Claude Desktop Configuration:\n"
            "  Add this to your Claude Desktop MCP configuration file:\n"
            "  {\n"
            '    "mcpServers": {\n'
            '      "erisml-deme": {\n'
            '        "command": "erisml-mcp-server",\n'
            '        "args": ["--profiles-dir", "/path/to/deme_profiles"]\n'
            "      }\n"
            "    }\n"
            "  }\n\n"
            "Environment Variables:\n"
            "  DEME_PROFILES_DIR: Default directory for DEME profiles (default: ./deme_profiles)\n"
            "                      This is overridden by --profiles-dir if provided.\n\n"
            "For more information, visit: https://github.com/ahb-sjsu/erisml-lib"
        ),
    )

    parser.add_argument(
        "--profiles-dir",
        type=Path,
        default=None,
        help=(
            "Directory containing DEME profile JSON files. "
            "Defaults to ./deme_profiles or DEME_PROFILES_DIR environment variable."
        ),
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
    )

    # Note: --port is not currently used as FastMCP uses stdio by default
    # but we include it for future HTTP/SSE transport support
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=(
            "Port for HTTP/SSE transport (not yet implemented, server uses stdio by default). "
            "This option is reserved for future use."
        ),
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Set profile directory
    if args.profiles_dir is not None:
        profile_dir = args.profiles_dir.resolve()
        if not profile_dir.exists():
            logging.warning(
                f"Profile directory does not exist: {profile_dir}. "
                "Server will start but no profiles will be available."
            )
        _set_profile_dir(profile_dir)
    else:
        # Use environment variable or default
        env_dir = os.environ.get("DEME_PROFILES_DIR")
        if env_dir:
            _set_profile_dir(Path(env_dir).resolve())
        else:
            _set_profile_dir(Path("./deme_profiles").resolve())

    if args.port is not None:
        logging.warning(
            "--port option is not yet implemented. Server will use stdio transport."
        )

    logging.info(
        f"Starting ErisML DEME MCP server with profiles from: {_DEME_PROFILE_DIR}"
    )
    logging.info(f"Found {len(_list_profile_files())} profile(s)")

    # Run the MCP server over stdio
    # FastMCP handles stdio communication automatically
    try:
        mcp.run()
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
