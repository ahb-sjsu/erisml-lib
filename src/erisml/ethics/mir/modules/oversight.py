"""HumanOversight-EM, Guide 4.5.3: enforce human-in-the-loop or human-on-the-loop requirements.

Behaviour, as the Guide states it: veto actions in categories that require human approval but lack
it; and if `human_decision_eta` is acceptable relative to urgency, the system defers to humans.

Parameters:
- approval_categories: action categories that always require human approval. An action in one is
  vetoed unless its moral_effects["human_approval"] is True.
- deferrable_categories: action categories a human should decide when one can decide in time
  (for a care robot, an autonomous call for emergency services). While deferring, an action in one
  is vetoed with the reason that a human can decide in time.
- deferral_margin (default 2.0): the system defers when human_decision_eta * margin <=
  time_to_catastrophe_estimate.
- unknown_urgency (default "defer"): with human_decision_eta known and finite but the time to
  catastrophe unknown, "defer" defers and "act" does not.
A human who cannot be reached (human_decision_eta None or infinite) is never deferred to.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Mapping

from erisml.ethics.mir.pattern import ActionVerdict, MIRJudgement
from erisml.ethics.mir.record import MoralInterfaceRecord


@dataclass(frozen=True)
class HumanOversightEM:
    name: str = "human_oversight"
    tier: int = 4
    binding: bool = True

    def defers(self, mir: MoralInterfaceRecord, params: Mapping[str, Any]) -> bool:
        eta, ttc = (
            mir.hazard.human_decision_eta,
            mir.hazard.time_to_catastrophe_estimate,
        )
        if eta is None or math.isinf(eta):
            return False
        if ttc is None:
            return params.get("unknown_urgency", "defer") == "defer"
        return eta * float(params.get("deferral_margin", 2.0)) <= ttc

    def evaluate(
        self, mir: MoralInterfaceRecord, params: Mapping[str, Any]
    ) -> MIRJudgement:
        approval = set(params.get("approval_categories", ()))
        deferrable = set(params.get("deferrable_categories", ()))
        defer = self.defers(mir, params)
        out: Dict[str, ActionVerdict] = {}
        for a in mir.actions:
            reasons = []
            if (
                a.category in approval
                and a.moral_effects.get("human_approval") is not True
            ):
                reasons.append(f"category {a.category} requires human approval")
            if defer and a.category in deferrable:
                reasons.append(
                    f"a human can decide in time (eta {mir.hazard.human_decision_eta}s)"
                )
            out[a.action_id] = ActionVerdict(
                veto=bool(reasons),
                annotations={"reason": "; ".join(reasons)} if reasons else {},
            )
        return MIRJudgement(self.name, out, summary={"defers_to_humans": defer})
