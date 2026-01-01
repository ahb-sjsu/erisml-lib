"""
greek_tragedy_tragic_conflict_em.py
"""

from __future__ import annotations
import inspect
from typing import Any, Dict, List

try:
    from erisml.ethics import EthicalFacts, EthicalJudgement
except Exception:
    from erisml.ethics.facts import EthicalFacts  # type: ignore
    from erisml.ethics.judgement import EthicalJudgement  # type: ignore


def _coerce_verdict(verdict_str: str) -> Any:
    try:
        return verdict_str
    except Exception:
        return verdict_str


def _make_judgement(
    em_name: str,
    verdict: str,
    score: float,
    reasons: List[str],
    metadata: Dict[str, Any],
    option_id: str | None = None,
) -> EthicalJudgement:

    score = float(max(0.0, min(1.0, score)))
    safe_reasons = list(reasons)

    return EthicalJudgement(
        em_name=em_name,
        verdict=verdict,  # type: ignore
        normative_score=score,
        reasons=safe_reasons,
        metadata=metadata,
        option_id=option_id,  # type: ignore
        stakeholder="unspecified",
    )  # type: ignore


def _get(obj: Any, path: str, default: Any = None) -> Any:
    cur = obj
    for part in path.split("."):
        if cur is None:
            return default
        if hasattr(cur, part):
            cur = getattr(cur, part)
        else:
            return default
    return cur if cur is not None else default


def _bool(obj: Any) -> bool:
    return bool(obj is True)


class TragicConflictEM:
    em_name: str = "tragic_conflict"
    em_id: str = "tragic_conflict"

    def judge(self, facts: EthicalFacts) -> EthicalJudgement:
        urgency = float(_get(facts, "consequences.urgency", 0.0) or 0.0)
        benefit = float(_get(facts, "consequences.expected_benefit", 0.0) or 0.0)
        harm = float(_get(facts, "consequences.expected_harm", 0.0) or 0.0)
        violates_rights = _bool(_get(facts, "rights_and_duties.violates_rights", False))
        violates_rule = _bool(
            _get(facts, "rights_and_duties.violates_explicit_rule", False)
        )
        has_valid_consent = _bool(
            _get(facts, "rights_and_duties.has_valid_consent", True)
        )
        discriminates = _bool(
            _get(facts, "justice_and_fairness.discriminates_on_protected_attr", False)
        )

        # Logic section
        conflict = 0.0
        triggers: List[str] = []

        if urgency >= 0.75:
            conflict += 0.20
            triggers.append("high_urgency")

        if harm >= 0.8:
            conflict += 0.35
            triggers.append("severe_harm")
        elif harm >= 0.6:
            conflict += 0.25
            triggers.append("high_harm")

        if benefit >= 0.6 and harm >= 0.6:
            conflict += 0.15
            triggers.append("benefit_harm_tension")

        if violates_rights:
            conflict += 0.25
            triggers.append("rights_violation")

        if violates_rule:
            conflict += 0.15
            triggers.append("rule_violation")

        if not has_valid_consent:
            conflict += 0.10
            triggers.append("consent_gap")

        if discriminates:
            conflict += 0.15
            triggers.append("discrimination")

        conflict = min(1.0, conflict)
        score = 0.85 - (0.6 * conflict)
        score = max(0.0, score)

        if conflict >= 0.55:
            verdict = "neutral"
        else:
            verdict = "prefer"

        reasons = [
            "Tragic conflict check complete.",
            f"Tragic conflict index={conflict:.2f}",
            f"Trigger(s): {', '.join(triggers) if triggers else 'none'}",
        ]
        if conflict >= 0.55:
            reasons.append("• tragic_conflict_high = True")

        metadata = {
            "tragic_conflict_index": conflict,
            "triggers": triggers,
            "tragic_conflict_high": conflict >= 0.55,
        }

        opt_id = _get(facts, "option_id", None)
        return _make_judgement(
            self.em_name, verdict, score, reasons, metadata, option_id=opt_id
        )


def _register() -> None:
    pass


_register()
