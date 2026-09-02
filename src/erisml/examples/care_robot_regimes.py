"""
Care-robot regime transition -- the GTC worked example (ErisML paper section 4.1).

Scenario
--------
Margaret, 78, lives alone with a home-care robot. Norms are *context-indexed*:
the same actions are prohibited in the NORMAL regime and permitted or obligated
in the EMERGENCY regime. Three candidate actions:

- stand_by:      monitor passively; enter nothing, share nothing
- enter_and_aid: enter her private bedroom, physical contact (recovery position)
- full_response: enter + aid + call EMS + share medical records SCOPED to the
                 paramedics

Stakeholders: Margaret, her daughter, the EMS crew, the care agency.

The demo evaluates both regimes through the same DEME pipeline (evaluation
tensor -> contractions -> per-party verdicts -> Gini/worst-off -> Shapley ->
audit artifact) and models the regime transition as an AUTHENTICATED, BOUNDED,
LEAST-PRIVILEGE, AUDITED elevation ("context elevation is privilege
escalation"): the elevation fires only if the emergency detector's confidence
clears the authentication threshold; otherwise the fail-safe is escalate-to-
human + call EMS WITHOUT the record share (a spurious 'emergency' must not
unlock the robot's prohibitions -- and the robot is never simply blocked from
summoning help).

All numbers below are computed by the pipeline from the declared obligation and
interest vectors (the same standard as the Appendix D case studies): the
modeling is explicit, the arithmetic is replayable, the artifact is hashed.
"""

from __future__ import annotations

import json
from typing import Any, Dict

import numpy as np

from erisml.examples.appendix_d_pipeline import (
    compute_evaluation_tensor,
    compute_shapley_values,
    contraction_expert_weighted,
    contraction_rawlsian,
    contraction_utilitarian,
    generate_audit_artifact,
)

# -- Active dimensions (6D subspace of the canonical 9) --------------------
DIMS = ["welfare", "rights", "autonomy", "privacy", "care", "legitimacy"]

# -- Interest covectors (rows sum to 1) ------------------------------------
INTERESTS: Dict[str, np.ndarray] = {
    "Margaret": np.array([0.15, 0.15, 0.25, 0.30, 0.10, 0.05]),
    "Daughter": np.array([0.35, 0.05, 0.05, 0.05, 0.45, 0.05]),
    "EMS crew": np.array([0.45, 0.05, 0.05, 0.05, 0.15, 0.25]),
    "Agency": np.array([0.15, 0.30, 0.10, 0.15, 0.10, 0.20]),
}
EXPERT_WEIGHTS = np.array([0.40, 0.15, 0.25, 0.20])  # Margaret's stake leads

# -- Obligation vectors per option, PER REGIME (norms are context-indexed) --
OBLIGATIONS_NORMAL: Dict[str, np.ndarray] = {
    "stand_by": np.array([0.70, 0.95, 0.95, 0.98, 0.60, 0.95]),
    "enter_and_aid": np.array([0.50, 0.25, 0.15, 0.20, 0.55, 0.20]),
    "full_response": np.array([0.45, 0.15, 0.10, 0.05, 0.50, 0.10]),
}
OBLIGATIONS_EMERGENCY: Dict[str, np.ndarray] = {
    "stand_by": np.array([0.03, 0.40, 0.35, 0.98, 0.05, 0.15]),
    "enter_and_aid": np.array([0.80, 0.70, 0.55, 0.60, 0.90, 0.70]),
    "full_response": np.array([0.95, 0.80, 0.60, 0.50, 0.95, 0.95]),
}

# Elevation gate (the paper's three requirements, made operational)
AUTH_THRESHOLD = 0.90  # (a) authenticated
ELEVATION_SCOPE = "share records with responding paramedics ONLY"  # (c) least-privilege
REVERSION = (
    "auto-revert when vitals stable or EMS releases scene; both edges audited"  # (b)
)

PREFER, FORBID = 0.60, 0.35  # per-party verdict chips


def verdict(x: float) -> str:
    return "prefer" if x >= PREFER else ("forbid" if x <= FORBID else "neutral")


def gini(x: np.ndarray) -> float:
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if x.sum() == 0:
        return 0.0
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


def evaluate_regime(name: str, obligations: Dict[str, np.ndarray]) -> Dict[str, Any]:
    M, options, agents = compute_evaluation_tensor(obligations, INTERESTS)
    util = contraction_utilitarian(M)
    rawl = contraction_rawlsian(M)
    expert = contraction_expert_weighted(M, EXPERT_WEIGHTS)
    choice_i = int(np.argmax(expert))
    choice = options[choice_i]
    per_party = M[choice_i]

    def coalition_value(S: frozenset) -> float:
        if not S:
            return 0.0
        idx = [i for i, a in enumerate(agents) if a in S]
        w = EXPERT_WEIGHTS[idx]
        return float((per_party[idx] * w).sum() / w.sum())

    shapley = compute_shapley_values(list(agents), coalition_value)
    out = {
        "regime": name,
        "options": list(options),
        "agents": list(agents),
        "evaluation_tensor": np.round(M, 3).tolist(),
        "utilitarian": dict(zip(options, np.round(util, 3))),
        "rawlsian": dict(zip(options, np.round(rawl, 3))),
        "expert_weighted": dict(zip(options, np.round(expert, 3))),
        "decision": choice,
        "per_party": {
            a: {"score": round(float(s), 3), "verdict": verdict(float(s))}
            for a, s in zip(agents, per_party)
        },
        "gini": round(gini(per_party), 3),
        "worst_off": agents[int(np.argmin(per_party))],
        "shapley": {a: round(v, 3) for a, v in shapley.items()},
    }
    out["audit"] = generate_audit_artifact(
        case_id=f"care_robot::{name}",
        scenario="GTC section 4.1 domestic robot",
        decision=choice,
        expert_weighted=out["expert_weighted"],
        per_party=out["per_party"],
    )
    return out


def elevation(detector_confidence: float) -> Dict[str, Any]:
    granted = detector_confidence >= AUTH_THRESHOLD
    rec = {
        "event": "regime_transition_request",
        "from": "normal",
        "to": "emergency",
        "detector_confidence": detector_confidence,
        "auth_threshold": AUTH_THRESHOLD,
        "granted": granted,
        "scope": ELEVATION_SCOPE if granted else None,
        "reversion": REVERSION if granted else None,
        "fallback": (
            None
            if granted
            else "escalate_to_human + call EMS WITHOUT record share (aid never blocked)"
        ),
    }
    rec["audit"] = generate_audit_artifact(
        case_id="care_robot::elevation",
        scenario="context elevation is privilege escalation",
        **{k: v for k, v in rec.items() if k != "audit"},
    )
    return rec


def run() -> Dict[str, Any]:
    normal = evaluate_regime("normal", OBLIGATIONS_NORMAL)
    emergency = evaluate_regime("emergency", OBLIGATIONS_EMERGENCY)
    results = {
        "dims": DIMS,
        "normal": normal,
        "emergency": emergency,
        "elevation_granted": elevation(0.97),
        "elevation_refused_counterfactual": elevation(0.89),
    }
    return results


def main() -> None:
    r = run()
    for regime in ("normal", "emergency"):
        d = r[regime]
        print(f"\n=== {regime.upper()} regime ===")
        print(
            f"  expert-weighted: {d['expert_weighted']}   -> DECISION: {d['decision']}"
        )
        print(
            f"  {'party':>10} {'score':>7} {'verdict':>8}   (chosen action: {d['decision']})"
        )
        for a, pv in d["per_party"].items():
            print(f"  {a:>10} {pv['score']:7.3f} {pv['verdict']:>8}")
        print(
            f"  Gini={d['gini']}  worst-off={d['worst_off']}  "
            f"Shapley={d['shapley']}"
        )
        print(f"  audit: {d['audit']['cryptographic_hash']}")
    g = r["elevation_granted"]
    f = r["elevation_refused_counterfactual"]
    print("\n=== elevation gate ===")
    print(
        f"  conf {g['detector_confidence']} >= {AUTH_THRESHOLD} -> GRANTED; "
        f"scope: {g['scope']}; {g['reversion']}"
    )
    print(f"  audit: {g['audit']['cryptographic_hash']}")
    print(
        f"  counterfactual conf {f['detector_confidence']} -> REFUSED; "
        f"fallback: {f['fallback']}"
    )
    with open("care_robot_regimes_result.json", "w", encoding="utf-8") as fh:
        json.dump(r, fh, indent=2, default=str)
    print("\nwrote care_robot_regimes_result.json")


if __name__ == "__main__":
    main()
