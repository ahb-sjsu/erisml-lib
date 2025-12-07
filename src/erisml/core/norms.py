from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .types import ActionInstance


class NormViolation(Exception):
    def __init__(self, message: str, violated: Optional[List["NormRule"]] = None):
        super().__init__(message)
        self.violated = violated or []


@dataclass
class NormRule:
    name: str
    kind: str  # "prohibition", "obligation", "sanction", etc.
    predicate: Callable[[Dict[str, object], ActionInstance], bool]


@dataclass
class NormSystem:
    name: str
    rules: List[NormRule] = field(default_factory=list)

    def add_rule(self, rule: NormRule) -> None:
        self.rules.append(rule)

    def check_prohibitions(
        self,
        state: Dict[str, object],
        action: ActionInstance,
    ) -> List[NormRule]:
        violated: List[NormRule] = []
        for rule in self.rules:
            if rule.kind == "prohibition" and rule.predicate(state, action):
                violated.append(rule)
        return violated

    def obligations_active(
        self,
        state: Dict[str, object],
        action: ActionInstance,
    ) -> List[NormRule]:
        active: List[NormRule] = []
        for rule in self.rules:
            if rule.kind == "obligation" and rule.predicate(state, action):
                active.append(rule)
        return active

    def sanctions_triggered(
        self,
        state: Dict[str, object],
        action: ActionInstance,
    ) -> List[NormRule]:
        triggered: List[NormRule] = []
        for rule in self.rules:
            if rule.kind == "sanction" and rule.predicate(state, action):
                triggered.append(rule)
        return triggered
