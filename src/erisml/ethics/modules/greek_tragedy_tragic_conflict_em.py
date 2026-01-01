"""
greek_tragedy_tragic_conflict_em.py
"""
from __future__ import annotations
from typing import Any, Dict, List

try:
    from erisml.ethics import EthicalFacts, EthicalJudgement
except Exception:
    from erisml.ethics.facts import EthicalFacts  # type: ignore
    from erisml.ethics.judgement import EthicalJudgement  # type: ignore

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
        verdict=verdict, # type: ignore
        normative_score=score,
        reasons=safe_reasons,
        metadata=metadata,
        option_id=option_id, # type: ignore
        stakeholder="unspecified"
    ) # type: ignore

def _get(obj: Any, path: str, default: Any = None) -> Any:
    cur = obj
    for part in path.split("."):
        if cur is None: return default
        if hasattr(cur, part): cur = getattr(cur, part)
        else: return default
    return cur if cur is not None else default

class TragicConflictEM:
    em_name: str = "tragic_conflict"
    em_id: str = "tragic_conflict"

    def judge(self, facts: EthicalFacts) -> EthicalJudgement:
        urgency = float(_get(facts, "consequences.urgency", 0.0) or 0.0)
        
        # Logic section
        conflict = 0.0
        triggers: List[str] = []

        if urgency >= 0.75:
            conflict += 0.25
            triggers.append("high_urgency")
        
        score = 0.8 - (0.5 * conflict)
        score = max(0.0, score)

        if conflict >= 0.5:
            verdict = "neutral"
        else:
            verdict = "prefer"

        reasons = ["Tragic conflict check complete.", f"Conflict index: {conflict}"]
        
        metadata = {
            "tragic_conflict_index": conflict,
            "triggers": triggers,
        }
        
        opt_id = _get(facts, "option_id", None)
        return _make_judgement(self.em_name, verdict, score, reasons, metadata, option_id=opt_id)

def _register() -> None:
    pass

_register()