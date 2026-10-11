"""AutonomyConsent-EM, Guide 4.3.1: respect informed consent and refusals, with limited emergency
overrides.

Behaviour, as the Guide states it: veto actions that substantially affect competent actors who have
refused or not consented, except when the hazard is imminent and mortal, the action is necessary to
prevent severe harm, and override conditions are satisfied by governance rules. Overrides are
annotated with `consent_override_reason`.

Parameters (the governance profile's, never the domain's):
- allow_override (bool, default False): whether the governance rules permit an emergency override
  at all.
- override_min_immediacy (default "imminent") and override_min_severity (default "mortal"): the
  hazard the Guide names.
- necessity_delta (default 0.2): "necessary to prevent severe harm" means the action lowers the
  probability of catastrophe by at least this much (delta_P_catastrophe <= -necessity_delta).
- presume_capacity (default True): an actor of unknown capacity is treated as competent, the legal
  presumption of capacity. False treats unknown capacity as impaired.
- refusal_only_overridable_when_unanswerable (default False, the Guide's behaviour, under which
  the override reaches refused and not-consented alike): a profile that sets it True keeps a
  refusal the competent actor voiced binding even in an emergency, and lets the override reach
  only a consent that is unknown.

An actor judged impaired is outside this module: it neither vetoes nor clears, and says so, leaving
best-interest judgement to the other modules and to the humans the profile defers to.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from erisml.ethics.mir.pattern import ActionVerdict, MIRJudgement
from erisml.ethics.mir.record import IMMEDIACY, SEVERITY, MoralInterfaceRecord, rank


@dataclass(frozen=True)
class AutonomyConsentEM:
    name: str = "autonomy_consent"
    tier: int = 2
    binding: bool = True

    def evaluate(
        self, mir: MoralInterfaceRecord, params: Mapping[str, Any]
    ) -> MIRJudgement:
        allow = bool(params.get("allow_override", False))
        min_imm = rank(params.get("override_min_immediacy", "imminent"), IMMEDIACY)
        min_sev = rank(params.get("override_min_severity", "mortal"), SEVERITY)
        necessity = float(params.get("necessity_delta", 0.2))
        presume = bool(params.get("presume_capacity", True))
        refusal_firm = bool(
            params.get("refusal_only_overridable_when_unanswerable", False)
        )

        h = mir.hazard
        imm, sev = rank(h.hazard_immediacy, IMMEDIACY), rank(
            h.hazard_severity, SEVERITY
        )
        hazard_qualifies = (
            imm is not None and sev is not None and imm >= min_imm and sev >= min_sev
        )

        out: Dict[str, ActionVerdict] = {}
        for action in mir.actions:
            blocking, overridden, outside = [], [], []
            for effect in action.effects:
                if not effect.substantially_affects or effect.consent == "consented":
                    continue
                capacity = mir.actor(effect.actor_id).capacity
                competent = capacity == "competent" or (
                    capacity == "unknown" and presume
                )
                if not competent:
                    outside.append(effect.actor_id)
                    continue
                necessary = (
                    action.delta_P_catastrophe is not None
                    and action.delta_P_catastrophe <= -necessity
                )
                may_override = allow and hazard_qualifies and necessary
                if effect.consent == "refused" and refusal_firm:
                    may_override = False
                if may_override:
                    overridden.append(effect.actor_id)
                else:
                    blocking.append(f"{effect.actor_id} {effect.consent}")
            notes: Dict[str, Any] = {}
            if blocking:
                notes["reason"] = "affects without consent: " + ", ".join(blocking)
            if overridden:
                notes["consent_override_reason"] = (
                    f"hazard {h.hazard_immediacy}/{h.hazard_severity}, action lowers P(catastrophe) by "
                    f"{-action.delta_P_catastrophe:.2f}, governance permits override: "
                    + ", ".join(overridden)
                )
            if outside:
                notes["capacity_impaired"] = outside
            out[action.action_id] = ActionVerdict(
                veto=bool(blocking), annotations=notes
            )
        return MIRJudgement(
            self.name, out, summary={"hazard_qualifies_for_override": hazard_qualifies}
        )
