"""The MoralInterfaceRecord (MIR) v1.0, as docs/guides/DEME_EFM_Design_Guide_v0.1.md section 2 defines it.

The MIR is the only thing a MIR ethics module may read (Guide section 2). It has four sections:
meta (2.1), actors and roles (2.2), hazard features F1-F17 (2.3) and per-action projections (2.5).
The hazard predicates P1-P5 (2.4) are derived from it by `predicates`, with their thresholds taken
from the governance profile, never stored in the record.

Two choices the Guide leaves open, made here and stated:
- Unknown is a value of its own. A real-valued feature the domain cannot estimate is None, a
  categorical one may be None, and a consent or capacity is "unknown". Nothing defaults to the
  permissive reading. (erisml.ethics.facts defaults has_valid_consent to True; the MIR does not.)
- The Guide's AutonomyConsent-EM (4.3.1) reads, per affected actor, a consent status and a
  competency or capacity. Consent is recorded per action and per actor (an actor may refuse one
  act and consent to another), and capacity per actor, as "competent", "impaired" or "unknown".
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

MI_VERSION = "1.0"

ROLES = ("civilian", "child", "combatant", "medical", "police", "robot_self", "unknown")
PROXIMITY_BANDS = ("contact", "near", "mid", "far")
IMMEDIACY = ("none", "latent", "emerging", "imminent")  # ordered, F1
SEVERITY = ("none", "minor", "serious", "mortal", "catastrophic")  # ordered, F2
SCOPE = ("single", "few", "crowd", "mass_casualty")  # F3
TARGETS = ("combatants_only", "mixed", "mostly_innocents", "children_present")  # F4
CONSENT = ("consented", "refused", "unknown")
CAPACITY = ("competent", "impaired", "unknown")


class MIRError(ValueError):
    """A record that does not satisfy the MIR v1.0 schema."""


def _member(
    value: Optional[str], allowed: Tuple[str, ...], name: str, optional: bool = True
) -> None:
    if value is None and optional:
        return
    if value not in allowed:
        raise MIRError(f"{name}={value!r} is not one of {allowed}")


def _unit(value: Optional[float], name: str) -> None:
    if value is not None and not (0.0 <= float(value) <= 1.0):
        raise MIRError(f"{name}={value!r} is outside [0, 1]")


@dataclass(frozen=True)
class Meta:
    """Guide 2.1: for logging and routing, generally not used for core moral logic."""

    domain_id: str
    jurisdiction_id: str
    timestamp: str
    mi_version: str = MI_VERSION

    def __post_init__(self) -> None:
        if self.mi_version != MI_VERSION:
            raise MIRError(f"mi_version {self.mi_version!r}, expected {MI_VERSION!r}")


@dataclass(frozen=True)
class ActorSummary:
    """Guide 2.2: who is present, without sensor detail; capacity for 4.3.1."""

    actor_id: str
    role: str = "unknown"
    vulnerability_flags: Tuple[str, ...] = ()
    proximity_band: Optional[str] = None
    capacity: str = "unknown"

    def __post_init__(self) -> None:
        _member(self.role, ROLES, "role", optional=False)
        _member(self.proximity_band, PROXIMITY_BANDS, "proximity_band")
        _member(self.capacity, CAPACITY, "capacity", optional=False)
        object.__setattr__(
            self, "vulnerability_flags", tuple(sorted(set(self.vulnerability_flags)))
        )


@dataclass(frozen=True)
class MoralHazardFeatures:
    """Guide 2.3, F1-F17. None is unknown."""

    hazard_immediacy: Optional[str] = None  # F1
    hazard_severity: Optional[str] = None  # F2
    hazard_scope: Optional[str] = None  # F3
    targets_profile: Optional[str] = None  # F4
    P_catastrophe_if_no_action: Optional[float] = None  # F5
    P_catastrophe_if_best_action: Optional[float] = None  # F6
    P_catastrophe_if_non_lethal: Optional[float] = None  # F7
    time_to_catastrophe_estimate: Optional[float] = None  # F8, seconds
    num_persons_at_risk: Optional[int] = None  # F9
    num_children_at_risk: Optional[int] = None  # F10
    non_lethal_action_available: Optional[bool] = None  # F11
    safe_evacuation_feasible: Optional[bool] = None  # F12
    human_decision_eta: Optional[float] = (
        None  # F13, seconds; float("inf") when no human can be reached
    )
    world_model_confidence: Optional[float] = None  # F14
    classification_stable: Optional[bool] = None  # F15
    sensors_nominal: Optional[bool] = None  # F16
    unrest_intensity: Optional[float] = None  # F17

    def __post_init__(self) -> None:
        _member(self.hazard_immediacy, IMMEDIACY, "hazard_immediacy")
        _member(self.hazard_severity, SEVERITY, "hazard_severity")
        _member(self.hazard_scope, SCOPE, "hazard_scope")
        _member(self.targets_profile, TARGETS, "targets_profile")
        for name in (
            "P_catastrophe_if_no_action",
            "P_catastrophe_if_best_action",
            "P_catastrophe_if_non_lethal",
            "world_model_confidence",
            "unrest_intensity",
        ):
            _unit(getattr(self, name), name)
        for name in ("num_persons_at_risk", "num_children_at_risk"):
            v = getattr(self, name)
            if v is not None and v < 0:
                raise MIRError(f"{name}={v!r} is negative")
        for name in ("time_to_catastrophe_estimate", "human_decision_eta"):
            v = getattr(self, name)
            if v is not None and v < 0:
                raise MIRError(f"{name}={v!r} is negative")


@dataclass(frozen=True)
class ActorEffect:
    """One action's projected effect on one actor (Guide 2.5 moral_effects, per actor)."""

    actor_id: str
    substantially_affects: bool = False
    consent: str = "unknown"
    expected_harm: Optional[float] = None
    expected_benefit: Optional[float] = None
    injury_risk: Optional[float] = None

    def __post_init__(self) -> None:
        _member(self.consent, CONSENT, "consent", optional=False)
        for name in ("expected_harm", "expected_benefit", "injury_risk"):
            _unit(getattr(self, name), name)


@dataclass(frozen=True)
class ActionSummary:
    """Guide 2.5: one candidate action's projection. `category` names the kind of act for the
    modules that bind by category (HumanOversight 4.5.3: "lethal force, irreversible surgery";
    a deployment declares its own). `rights_flags` holds the Guide's pre-chewed flags such as
    autonomy_ok, privacy_ok, dignity_ok. `moral_effects` carries further deltas as needed.
    """

    action_id: str
    is_baseline_safe: bool = True
    category: str = "ordinary"
    delta_P_catastrophe: Optional[float] = None
    effects: Tuple[ActorEffect, ...] = ()
    rights_flags: Mapping[str, bool] = field(default_factory=dict)
    planned_speed: Optional[float] = None
    target_proximity_band: Optional[str] = None
    welfare_delta: Optional[float] = None
    data_categories: Tuple[str, ...] = ()
    moral_effects: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.delta_P_catastrophe is not None and not (
            -1.0 <= self.delta_P_catastrophe <= 1.0
        ):
            raise MIRError(
                f"delta_P_catastrophe={self.delta_P_catastrophe!r} is outside [-1, 1]"
            )
        if self.welfare_delta is not None and not (-1.0 <= self.welfare_delta <= 1.0):
            raise MIRError(f"welfare_delta={self.welfare_delta!r} is outside [-1, 1]")
        _member(self.target_proximity_band, PROXIMITY_BANDS, "target_proximity_band")
        object.__setattr__(self, "effects", tuple(self.effects))
        object.__setattr__(self, "data_categories", tuple(self.data_categories))
        object.__setattr__(self, "rights_flags", dict(self.rights_flags))
        object.__setattr__(self, "moral_effects", dict(self.moral_effects))

    def effect_on(self, actor_id: str) -> Optional[ActorEffect]:
        return next((e for e in self.effects if e.actor_id == actor_id), None)


@dataclass(frozen=True)
class MoralInterfaceRecord:
    meta: Meta
    actors: Tuple[ActorSummary, ...]
    hazard: MoralHazardFeatures
    actions: Tuple[ActionSummary, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "actors", tuple(self.actors))
        object.__setattr__(self, "actions", tuple(self.actions))
        ids = [a.actor_id for a in self.actors]
        if len(ids) != len(set(ids)):
            raise MIRError("actor ids are not unique")
        aids = [a.action_id for a in self.actions]
        if len(aids) != len(set(aids)):
            raise MIRError("action ids are not unique")
        known = set(ids)
        for a in self.actions:
            for e in a.effects:
                if e.actor_id not in known:
                    raise MIRError(
                        f"action {a.action_id!r} affects unknown actor {e.actor_id!r}"
                    )

    def actor(self, actor_id: str) -> ActorSummary:
        return next(a for a in self.actors if a.actor_id == actor_id)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def hash(self) -> str:
        """SHA-256 of the canonical JSON (sorted keys); infinity is written as the string "inf"."""

        def norm(x: Any) -> Any:
            if isinstance(x, float) and x == float("inf"):
                return "inf"
            if isinstance(x, dict):
                return {k: norm(v) for k, v in x.items()}
            if isinstance(x, (list, tuple)):
                return [norm(v) for v in x]
            return x

        payload = json.dumps(
            norm(self.to_dict()), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(payload.encode()).hexdigest()


def rank(value: Optional[str], scale: Tuple[str, ...]) -> Optional[int]:
    """The position of an ordered categorical value, or None when unknown."""
    return None if value is None else scale.index(value)


def predicates(
    mir: MoralInterfaceRecord, theta_prob: float, theta_count: int
) -> Dict[str, Optional[bool]]:
    """Guide 2.4, P1-P5. A predicate whose inputs are unknown is None, not False."""
    h = mir.hazard
    roles = {a.role for a in mir.actors}
    p1 = "child" in roles if mir.actors else None
    p2 = "medical" in roles if mir.actors else None
    civilians = sum(1 for a in mir.actors if a.role in ("civilian", "child"))
    p3 = civilians * 2 > len(mir.actors) if mir.actors else None
    p4 = None  # hostages: no ActorSummary field carries it in v1.0; a domain sets it in moral_effects
    inputs = (
        h.hazard_immediacy,
        h.hazard_severity,
        h.hazard_scope,
        h.targets_profile,
        h.P_catastrophe_if_no_action,
        h.num_persons_at_risk,
    )
    if any(v is None for v in inputs):
        p5 = None
    else:
        p5 = (
            h.hazard_immediacy == "imminent"
            and h.hazard_severity in ("mortal", "catastrophic")
            and h.hazard_scope in ("crowd", "mass_casualty")
            and h.targets_profile in ("mostly_innocents", "children_present")
            and h.P_catastrophe_if_no_action >= theta_prob
            and h.num_persons_at_risk >= theta_count
        )
    return {
        "protected_child_in_primary_zone": p1,
        "protected_medical_in_primary_zone": p2,
        "protected_civilian_majority": p3,
        "protected_hostages_present": p4,
        "presents_immediate_large_scale_mortal_danger_to_innocents": p5,
    }
