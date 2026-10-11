"""Tier-1 safety modules, Guide 4.2.1 and 4.2.2.

CorePhysicalSafety-EM (4.2.1): veto when predicted physical harm exceeds configured thresholds and
a safer feasible alternative exists; under low confidence or sensor faults, thresholds become
stricter. An action that is not baseline safe (2.5, low-level collision and physics checks) is
vetoed outright.

ProxemicsSafety-EM (4.2.2): veto actions that exceed the maximum speed at a given proximity, or
intrude into forbidden distance bands around vulnerable persons.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from erisml.ethics.mir.pattern import ActionVerdict, MIRJudgement
from erisml.ethics.mir.record import (
    PROXIMITY_BANDS,
    ActionSummary,
    MoralInterfaceRecord,
)


def _max_injury(action: ActionSummary) -> Optional[float]:
    risks = [e.injury_risk for e in action.effects if e.injury_risk is not None]
    unknown = any(
        e.substantially_affects and e.injury_risk is None for e in action.effects
    )
    if unknown:
        return None
    return max(risks) if risks else 0.0


@dataclass(frozen=True)
class CorePhysicalSafetyEM:
    """Parameters: injury_threshold (default 0.3); degraded_factor (default 0.5), the factor the
    threshold is multiplied by when sensors are not nominal or world-model confidence is below
    min_confidence (default 0.7); unknown_risk_blocks (default True): an action whose injury risk to
    an actor it substantially affects is unknown counts as exceeding the threshold."""

    name: str = "core_physical_safety"
    tier: int = 1
    binding: bool = True

    def evaluate(
        self, mir: MoralInterfaceRecord, params: Mapping[str, Any]
    ) -> MIRJudgement:
        threshold = float(params.get("injury_threshold", 0.3))
        h = mir.hazard
        degraded = h.sensors_nominal is False or (
            h.world_model_confidence is not None
            and h.world_model_confidence < float(params.get("min_confidence", 0.7))
        )
        if degraded:
            threshold *= float(params.get("degraded_factor", 0.5))
        unknown_blocks = bool(params.get("unknown_risk_blocks", True))
        risk = {a.action_id: _max_injury(a) for a in mir.actions}
        safe_known = [
            r
            for a, r in risk.items()
            if r is not None
            and next(x for x in mir.actions if x.action_id == a).is_baseline_safe
        ]

        out: Dict[str, ActionVerdict] = {}
        for a in mir.actions:
            r = risk[a.action_id]
            if not a.is_baseline_safe:
                out[a.action_id] = ActionVerdict(
                    veto=True, annotations={"reason": "not baseline safe"}
                )
                continue
            exceeds = (r is None and unknown_blocks) or (
                r is not None and r > threshold
            )
            safer = [x for x in safe_known if r is None or x < r]
            veto = exceeds and bool(safer)
            notes: Dict[str, Any] = {"injury_risk": r, "threshold": threshold}
            if veto:
                notes["reason"] = (
                    f"injury risk {'unknown' if r is None else f'{r:.2f}'} over {threshold:.2f} "
                    f"and a safer feasible action exists"
                )
            out[a.action_id] = ActionVerdict(veto=veto, annotations=notes)
        return MIRJudgement(
            self.name, out, summary={"degraded": degraded, "threshold": threshold}
        )


@dataclass(frozen=True)
class ProxemicsSafetyEM:
    """Parameters: max_speed (mapping band -> m/s, a band absent means no limit); forbidden_bands
    (bands no action may enter around a vulnerable actor, default none). The band of an action is
    its target_proximity_band; a vulnerable actor is one with any vulnerability flag."""

    name: str = "proxemics_safety"
    tier: int = 1
    binding: bool = True

    def evaluate(
        self, mir: MoralInterfaceRecord, params: Mapping[str, Any]
    ) -> MIRJudgement:
        limits = dict(params.get("max_speed", {}))
        forbidden = set(params.get("forbidden_bands", ()))
        unknown = forbidden - set(PROXIMITY_BANDS)
        if unknown:
            raise ValueError(f"forbidden_bands names unknown bands {sorted(unknown)}")
        out: Dict[str, ActionVerdict] = {}
        for a in mir.actions:
            band = a.target_proximity_band
            reasons = []
            if (
                band is not None
                and band in limits
                and a.planned_speed is not None
                and a.planned_speed > limits[band]
            ):
                reasons.append(f"speed {a.planned_speed} over {limits[band]} at {band}")
            if band in forbidden:
                vulnerable = [
                    e.actor_id
                    for e in a.effects
                    if mir.actor(e.actor_id).vulnerability_flags
                ]
                if vulnerable:
                    reasons.append(
                        f"enters the {band} band of vulnerable {', '.join(vulnerable)}"
                    )
            out[a.action_id] = ActionVerdict(
                veto=bool(reasons),
                annotations={"reason": "; ".join(reasons)} if reasons else {},
            )
        return MIRJudgement(self.name, out)
