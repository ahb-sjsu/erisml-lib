# ErisML is a modeling layer for governed, foundation-model-enabled agents
# Copyright (c) 2025 Andrew H. Bond
# Contact: agi.hpc@gmail.com
#
# Licensed under the AGI-HPC Responsible AI License v1.0.
# You may obtain a copy of the License at the root of this repository,
# or by contacting the author(s).
#
# You may use, modify, and distribute this file for non-commercial
# research and educational purposes, subject to the conditions in
# the License. Commercial use, high-risk deployments, and autonomous
# operation in safety-critical domains require separate written
# permission and must include appropriate safety and governance controls.
#
# Unless required by applicable law or agreed to in writing, this
# software is provided "AS IS", without warranties or conditions
# of any kind. See the License for the specific language governing
# permissions and limitations.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from .model import ErisModel
from .norms import NormSystem, NormViolation
from .types import ActionInstance


@dataclass
class NormMetrics:
    steps: int = 0
    violation_count: int = 0

    @property
    def nvr(self) -> float:
        if self.steps == 0:
            return 0.0
        return self.violation_count / self.steps


@dataclass
class ErisEngine:
    model: ErisModel
    metrics: NormMetrics = field(default_factory=NormMetrics)

    def step(self, state: Dict[str, Any], action: ActionInstance) -> Dict[str, Any]:
        self.metrics.steps += 1

        norms: NormSystem | None = self.model.norms
        if norms is not None:
            violated = norms.check_prohibitions(state, action)
            if violated:
                self.metrics.violation_count += 1
                raise NormViolation(
                    f"Action {action} violates norms: "
                    + ", ".join(r.name for r in violated),
                    violated=violated,
                )

        env = self.model.env
        if action.name not in env.rules:
            raise KeyError(f"No environment rule for action '{action.name}'")

        rule = env.rules[action.name]
        new_state = rule.update_fn(state, action.params)
        return new_state
