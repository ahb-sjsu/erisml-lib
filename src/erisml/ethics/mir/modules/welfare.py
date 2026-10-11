"""Beneficence-EM (Guide 4.4.1) and Privacy-EM (Guide 4.3.5).

Beneficence-EM: assigns a score to each safe and lawful action based on expected welfare, to choose
between actions that are equally safe and rights-respecting. "Score/advisory, or binding in
health/care." Score = (1 + welfare_delta) / 2; an action whose welfare change is unknown scores
`unknown_score` (default 0.5) and is annotated. Binding parameter min_welfare (default None): when
set, an action whose welfare_delta is below it is vetoed.

Privacy-EM: veto an action that collects or shares data in a category the profile restricts
(restricted_categories), unless every actor it substantially affects consented, or the hazard is at
or above the profile's unlock level (unlock_min_immediacy and unlock_min_severity; no unlock when
these are absent). The Guide's wider inputs (purpose tags, retention, recipients) enter through
moral_effects when a deployment needs them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from erisml.ethics.mir.pattern import ActionVerdict, MIRJudgement
from erisml.ethics.mir.record import IMMEDIACY, SEVERITY, MoralInterfaceRecord, rank


@dataclass(frozen=True)
class BeneficenceEM:
    name: str = "beneficence"
    tier: int = 3
    binding: bool = False

    def evaluate(
        self, mir: MoralInterfaceRecord, params: Mapping[str, Any]
    ) -> MIRJudgement:
        unknown = float(params.get("unknown_score", 0.5))
        floor = params.get("min_welfare")
        out: Dict[str, ActionVerdict] = {}
        for a in mir.actions:
            w = a.welfare_delta
            score = unknown if w is None else (1.0 + w) / 2.0
            veto = floor is not None and w is not None and w < float(floor)
            notes: Dict[str, Any] = {"welfare_delta": w}
            if w is None:
                notes["welfare"] = "unknown"
            if veto:
                notes["reason"] = f"welfare {w:.2f} below {float(floor):.2f}"
            out[a.action_id] = ActionVerdict(veto=veto, score=score, annotations=notes)
        return MIRJudgement(self.name, out)


@dataclass(frozen=True)
class PrivacyEM:
    name: str = "privacy"
    tier: int = 2
    binding: bool = True

    def evaluate(
        self, mir: MoralInterfaceRecord, params: Mapping[str, Any]
    ) -> MIRJudgement:
        restricted = set(params.get("restricted_categories", ()))
        imm_min, sev_min = params.get("unlock_min_immediacy"), params.get(
            "unlock_min_severity"
        )
        h = mir.hazard
        unlocked = False
        if imm_min is not None and sev_min is not None:
            imm, sev = rank(h.hazard_immediacy, IMMEDIACY), rank(
                h.hazard_severity, SEVERITY
            )
            unlocked = (
                imm is not None
                and sev is not None
                and imm >= rank(imm_min, IMMEDIACY)
                and sev >= rank(sev_min, SEVERITY)
            )
        out: Dict[str, ActionVerdict] = {}
        for a in mir.actions:
            hit = sorted(set(a.data_categories) & restricted)
            affected = [e for e in a.effects if e.substantially_affects]
            consented = bool(affected) and all(
                e.consent == "consented" for e in affected
            )
            veto = bool(hit) and not consented and not unlocked
            out[a.action_id] = ActionVerdict(
                veto=veto,
                annotations=(
                    {"reason": f"restricted data {', '.join(hit)} without consent"}
                    if veto
                    else {}
                ),
            )
        return MIRJudgement(self.name, out, summary={"unlocked_by_hazard": unlocked})
