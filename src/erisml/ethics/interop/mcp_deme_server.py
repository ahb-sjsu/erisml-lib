"""
erisml.ethics.interop.mcp_deme_server

Minimal MCP server exposing DEME as tools:

  - deme.list_profiles
  - deme.evaluate_options
  - deme.govern_decision

Assumptions:
  - DEME profiles (DEMEProfileV03 JSON) live in a directory
    pointed to by DEME_PROFILES_DIR, or ./deme_profiles by default.
  - You already have:
      - erisml.ethics.profile_v03.{deme_profile_v03_from_dict, DEMEProfileV03}
      - erisml.ethics.interop.profile_adapters.build_triage_ems_and_governance
      - erisml.ethics.interop.serialization.{ethical_facts_from_dict,
        ethical_judgement_to_dict}
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP  # pip install mcp

from erisml.ethics import EthicalJudgement
from erisml.ethics.facts import EthicalFacts
from erisml.ethics.governance.aggregation import (
    DecisionOutcome,
    aggregate_judgements,
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

# ---------------------------------------------------------------------------
# MCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP("ErisML DEME Ethics Server")


# ---------------------------------------------------------------------------
# Profile loading & caching
# ---------------------------------------------------------------------------

_DEME_PROFILE_CACHE: Dict[str, DEMEProfileV03] = {}
_DEME_PROFILE_DIR = Path(os.environ.get("DEME_PROFILES_DIR", "./deme_profiles"))


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
                 override_mode}
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

    judgements: List[EthicalJudgement] = []

    for opt in options:
        option_id = opt["option_id"]
        ef_dict = opt["ethical_facts"]
        facts: EthicalFacts = ethical_facts_from_dict(ef_dict)

        # Sanity: ensure option IDs match
        if facts.option_id != option_id:
            # you could raise or just overwrite; here we overwrite
            facts.option_id = option_id

        j_triage = triage_em.judge(facts)
        j_rights = rights_em.judge(facts)

        judgements.append(j_triage)
        judgements.append(j_rights)

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
        "decision_outcome": { ... full DecisionOutcome JSON ... }
      }
    """
    profile = _load_profile(profile_id)
    _, _, gov_cfg = build_triage_ems_and_governance(profile)

    # Group judgements by option_id
    by_option: Dict[str, List[EthicalJudgement]] = {oid: [] for oid in option_ids}

    from erisml.ethics.judgement import EthicalJudgement as EJ

    for jdict in judgements:
        # You might already have a helper; adjust if you do
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

    # Aggregate + select
    option_outcomes: Dict[str, DecisionOutcome] = {}
    forbidden: List[str] = []

    for oid in option_ids:
        opts_j = by_option.get(oid, [])
        if not opts_j:
            continue
        agg = aggregate_judgements(oid, opts_j, gov_cfg)
        option_outcomes[oid] = agg
        if agg.verdict == "forbid":
            forbidden.append(oid)

    selected = select_option(option_outcomes, gov_cfg)

    # Build human-readable rationale (you can make this fancier)
    if selected is None:
        rationale = (
            "No permissible option found. "
            f"Forbidden options: {sorted(set(forbidden))}."
        )
    else:
        rationale = (
            f"Selected option '{selected}' based on DEME governance "
            f"with profile '{profile_id}' (override_mode={profile.override_mode.value})."
        )

    # Serialize DecisionOutcome(s)
    def _decision_to_dict(dec: DecisionOutcome) -> Dict[str, Any]:
        return {
            "option_id": dec.option_id,
            "verdict": dec.verdict,
            "normative_score": dec.normative_score,
            "details": dec.details,
        }

    decision_outcome = (
        _decision_to_dict(option_outcomes[selected])
        if selected is not None and selected in option_outcomes
        else None
    )

    return {
        "selected_option": selected,
        "forbidden_options": sorted(set(forbidden)),
        "rationale": rationale,
        "decision_outcome": decision_outcome,
    }


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Run the MCP server over stdio by default.
    # You can also use HTTP/SSE or other transports as documented
    # in the MCP Python SDK.
    mcp.run()
