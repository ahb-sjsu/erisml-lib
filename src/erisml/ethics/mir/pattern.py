"""MIR ethics modules and their composition, as Guide sections 3.1 and 5.3 define them.

A MIR ethics module is a pure function E(MIR, params) returning, per action, a veto, a soft block,
an optional score and annotations, and globally a health flag and a summary (Guide 3.1).

The lexicographic stack (Guide 5.3) runs levels in strict priority. At each level the binding
modules may veto actions outright; the level then keeps the subset that best satisfies it, by the
scores of its modules, and passes only that subset on. No lower level can reintroduce an action a
higher level removed.

Choices the Guide leaves open, made here and stated:
- A soft block is kept, not removed: it marks an action that needs a human's authorization
  (JurisdictionalLaw 4.2.4). The result lists it; the caller obtains the authorization or moves on.
- A module that raises vetoes every action still standing at its level and sets health_ok false,
  as a failing module vetoes under the tactical layer's fail_closed: an action nobody could judge
  is not passed as judged.
- "Best satisfies the level": an action survives when its level score (the mean of the scores of
  that level's scoring modules) is within `tolerance` of the best. A level whose modules give no
  scores keeps every action they did not veto.
- Order is deterministic: survivors keep the order in which the MIR lists the actions, then are
  ranked by the last scoring level's score, best first.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence, Tuple

from erisml.ethics.mir.record import MoralInterfaceRecord


@dataclass(frozen=True)
class ActionVerdict:
    veto: bool = False
    soft_block: bool = False
    score: Optional[float] = None
    annotations: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MIRJudgement:
    em_name: str
    per_action: Mapping[str, ActionVerdict]
    health_ok: bool = True
    summary: Mapping[str, Any] = field(default_factory=dict)


class MIREthicsModule(Protocol):
    """Guide 3.1. `binding` modules may veto; advisory modules only score and annotate."""

    name: str
    tier: int
    binding: bool

    def evaluate(
        self, mir: MoralInterfaceRecord, params: Mapping[str, Any]
    ) -> MIRJudgement: ...


@dataclass(frozen=True)
class ModuleSlot:
    """A module placed in a pattern with its profile parameters."""

    module: MIREthicsModule
    params: Mapping[str, Any] = field(default_factory=dict)
    binding: Optional[bool] = None  # None: the module's own default

    @property
    def is_binding(self) -> bool:
        return self.module.binding if self.binding is None else self.binding


@dataclass(frozen=True)
class Level:
    name: str
    slots: Tuple[ModuleSlot, ...]
    tolerance: float = 1e-9


@dataclass
class LevelTrace:
    name: str
    entered: List[str]
    vetoed: Dict[str, List[str]]
    kept: List[str]
    scores: Dict[str, float]
    failures: List[str]


@dataclass
class PatternResult:
    ranked: List[str]
    vetoed: Dict[str, List[str]]
    soft_blocked: Dict[str, List[str]]
    annotations: Dict[str, Dict[str, Any]]
    health_ok: bool
    trace: List[LevelTrace]
    mir_hash: str

    @property
    def selected(self) -> Optional[str]:
        return self.ranked[0] if self.ranked else None


def run_lexicographic(
    mir: MoralInterfaceRecord, levels: Sequence[Level]
) -> PatternResult:
    order = [a.action_id for a in mir.actions]
    standing = list(order)
    vetoed: Dict[str, List[str]] = {}
    soft: Dict[str, List[str]] = {}
    notes: Dict[str, Dict[str, Any]] = {a: {} for a in order}
    health_ok = True
    trace: List[LevelTrace] = []
    last_scores: Dict[str, float] = {}

    for level in levels:
        entered = list(standing)
        level_vetoes: Dict[str, List[str]] = {}
        sums: Dict[str, float] = {}
        counts: Dict[str, int] = {}
        failures: List[str] = []
        for slot in level.slots:
            name = slot.module.name
            try:
                judgement = slot.module.evaluate(mir, slot.params)
            except Exception as e:  # fail closed: nobody judged these actions
                failures.append(f"{name}: {type(e).__name__}: {e}")
                health_ok = False
                for a in entered:
                    level_vetoes.setdefault(a, []).append(
                        f"{name}: failed ({type(e).__name__})"
                    )
                continue
            if not judgement.health_ok:
                health_ok = False
            for a in entered:
                v = judgement.per_action.get(a)
                if v is None:
                    if (
                        slot.is_binding
                    ):  # a binding module that says nothing about an action has not cleared it
                        level_vetoes.setdefault(a, []).append(f"{name}: no verdict")
                    continue
                if v.annotations:
                    notes[a][name] = dict(v.annotations)
                if v.veto and slot.is_binding:
                    reason = v.annotations.get("reason", "veto")
                    level_vetoes.setdefault(a, []).append(f"{name}: {reason}")
                if v.soft_block and slot.is_binding:
                    soft.setdefault(a, []).append(
                        f"{name}: {v.annotations.get('reason', 'needs authorization')}"
                    )
                if v.score is not None:
                    sums[a] = sums.get(a, 0.0) + float(v.score)
                    counts[a] = counts.get(a, 0) + 1
        survivors = [a for a in entered if a not in level_vetoes]
        for a, reasons in level_vetoes.items():
            vetoed.setdefault(a, []).extend(reasons)
        scores = {a: sums[a] / counts[a] for a in survivors if a in counts}
        if scores:
            best = max(scores.values())
            survivors = [
                a
                for a in survivors
                if a in scores and scores[a] >= best - level.tolerance
            ]
            last_scores = scores
        trace.append(
            LevelTrace(
                level.name, entered, level_vetoes, list(survivors), scores, failures
            )
        )
        standing = survivors

    ranked = sorted(standing, key=lambda a: (-last_scores.get(a, 0.0), order.index(a)))
    return PatternResult(
        ranked,
        vetoed,
        soft,
        {a: n for a, n in notes.items() if n},
        health_ok,
        trace,
        mir.hash(),
    )
