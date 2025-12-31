"""
erisml.ethics.interop.mcp_deme_server

Minimal MCP server exposing DEME as tools:

  - list_profiles
  - evaluate_options
  - govern_decision

Assumptions:
  - DEME profiles (DEMEProfileV03 JSON) live in a directory
    pointed to by DEME_PROFILES_DIR, or ./deme_profiles by default.
  - You already have:
      - erisml.ethics.profile_v03.{deme_profile_v03_from_dict, DEMEProfileV03}
      - erisml.ethics.interop.profile_adapters.build_triage_ems_and_governance
      - erisml.ethics.interop.serialization.{ethical_facts_from_dict,
        ethical_judgement_to_dict}
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP  # pip install mcp

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


# ---------------------------------------------------------------------------
# MCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP("ErisML DEME Ethics Server")


# ---------------------------------------------------------------------------
# Profile loading & caching
# ---------------------------------------------------------------------------

_DEME_PROFILE_CACHE: Dict[str, DEMEProfileV03] = {}
_DEME_PROFILE_DIR: Path = Path(os.environ.get("DEME_PROFILES_DIR", "./deme_profiles"))


def _set_profile_dir(path: Path) -> None:
    """Set the profile directory and clear cache."""
    global _DEME_PROFILE_DIR
    _DEME_PROFILE_DIR = path
    _DEME_PROFILE_CACHE.clear()


def _load_profile(profile_id: str) -> DEMEProfileV03:
    """
    Very simple file-based profile loader.

    - profile_id is expected to match `${profile_id}.json` in DEME_PROFILES_DIR.
    - You can swap this out for a DB or API later.
    """
    if profile_id in _DEME_PROFILE_CACHE:
        return _DEME_PROFILE_CACHE[profile_id]

    path = _DEME_PROFILE_DIR / f"{profile_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"DEME profile '{profile_id}' not found at {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    profile = deme_profile_v03_from_dict(data)
    _DEME_PROFILE_CACHE[profile_id] = profile
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
                "This server provides three MCP tools:\n"
                "  - deme.list_profiles: List available DEME profiles\n"
                "  - deme.evaluate_options: Evaluate candidate options using ethics modules\n"
                "  - deme.govern_decision: Apply governance to aggregate EM judgements\n\n"
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
            "This server provides three MCP tools:\n"
            "  - deme.list_profiles: List available DEME profiles\n"
            "  - deme.evaluate_options: Evaluate candidate options using ethics modules\n"
            "  - deme.govern_decision: Apply governance to aggregate EM judgements\n\n"
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
