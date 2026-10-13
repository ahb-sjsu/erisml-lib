# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Composition patterns: the DAG shapes that wire EMs together (Design Guide v0.1, section 5).

A pattern is an ordered sequence of stages. Each stage runs the EMs it admits (by tier and
registry tag) on the options still standing, and then does some of three things:

- ``vetoes``: drops the options its binding EMs forbid (tier veto rights and governance
  apply);
- ``narrows``: keeps only the options that best satisfy the stage, those whose aggregate
  score is within ``tolerance`` of the best;
- ``ranks``: orders the survivors; the last stage that ranks and ran any EM decides the
  order.

No stage resurrects an option an earlier stage removed. The guide allows two or three
patterns per system (section 3.2); these are its three, plus the flat legacy shape:

- ``hard_shell`` (5.1): tiers 0 and 1 form a veto shell; tiers 2 to 4 judge and rank only
  the safe set.
- ``hard_shell_fairness`` (5.2): the same shell; then the welfare and rights EMs veto and
  narrow to the utility-filtered set; then the fairness EMs re-rank within it, and may not
  veto.
- ``lexicographic`` (5.3): one level per tier, highest priority first; each level vetoes and
  passes on only its best-satisfying subset; the last level ranks.
- ``flat``: every EM in one stage that vetoes and ranks (the pipeline before patterns).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Tuple

from erisml.ethics.modules.registry import EMRegistry

ALL_TIERS: FrozenSet[int] = frozenset(range(5))


def em_tags(em: Any) -> FrozenSet[str]:
    """An EM's tags: its ``em_tags`` attribute, else its registry entry's."""
    tags = getattr(em, "em_tags", None)
    if tags is None:
        entry = EMRegistry.get(type(em).__name__)
        tags = entry.tags if entry is not None else ()
    return frozenset(tags)


@dataclass(frozen=True)
class Stage:
    """One node of a pattern."""

    name: str
    tiers: FrozenSet[int] = ALL_TIERS
    tags: FrozenSet[str] = frozenset()
    """If given, the stage admits only EMs with at least one of these tags."""
    exclude_tags: FrozenSet[str] = frozenset()
    vetoes: bool = True
    narrows: bool = False
    ranks: bool = False

    def admits(self, em: Any) -> bool:
        if getattr(em, "em_tier", None) not in self.tiers:
            return False
        tags = em_tags(em)
        if self.tags and not (tags & self.tags):
            return False
        return not (tags & self.exclude_tags)


@dataclass(frozen=True)
class CompositionPattern:
    name: str
    stages: Tuple[Stage, ...]
    tolerance: float = 0.05
    """A narrowing stage keeps the options scoring within this of its best."""


FAIRNESS = frozenset({"fairness"})

FLAT = CompositionPattern("flat", (Stage("all", ranks=True),))

HARD_SHELL = CompositionPattern(
    "hard_shell",
    (
        Stage("shell", tiers=frozenset({0, 1})),
        Stage("inner", tiers=frozenset({2, 3, 4}), ranks=True),
    ),
)

HARD_SHELL_FAIRNESS = CompositionPattern(
    "hard_shell_fairness",
    (
        Stage("shell", tiers=frozenset({0, 1})),
        Stage(
            "welfare",
            tiers=frozenset({2, 3, 4}),
            exclude_tags=FAIRNESS,
            narrows=True,
            ranks=True,
        ),
        Stage(
            "fairness",
            tiers=frozenset({2, 3, 4}),
            tags=FAIRNESS,
            vetoes=False,
            ranks=True,
        ),
    ),
)

LEXICOGRAPHIC = CompositionPattern(
    "lexicographic",
    tuple(
        Stage(f"level_{t}", tiers=frozenset({t}), narrows=t < 4, ranks=True)
        for t in range(5)
    ),
)

PATTERNS: Dict[str, CompositionPattern] = {
    p.name: p for p in (FLAT, HARD_SHELL, HARD_SHELL_FAIRNESS, LEXICOGRAPHIC)
}


def resolve_pattern(pattern: Any) -> CompositionPattern:
    if pattern is None:
        return FLAT
    if isinstance(pattern, CompositionPattern):
        return pattern
    try:
        return PATTERNS[str(pattern)]
    except KeyError:
        raise ValueError(
            f"unknown composition pattern {pattern!r}; known: {sorted(PATTERNS)}"
        ) from None


__all__ = [
    "Stage",
    "CompositionPattern",
    "FLAT",
    "HARD_SHELL",
    "HARD_SHELL_FAIRNESS",
    "LEXICOGRAPHIC",
    "PATTERNS",
    "resolve_pattern",
    "em_tags",
]
