# ErisML is a modeling layer for governed, foundation-model-enabled agents
# Copyright (c) 2025 Andrew H. Bond
# Contact: agi.hpc@gmail.com
#
# Licensed under the MIT License. See LICENSE.txt at the root of this repository.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict

from erisml.core.norms import NormSystem, NormViolation
from erisml.core.model import ErisModel
from erisml.core.types import ActionInstance


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
    """
    Core agent runtime for ErisML models.

    Provides a standard agent-environment loop with:
    - Lifecycle methods (reset, step, close)
    - Observable hooks (pre_step, post_step)
    - Norm enforcement integration
    """

    model: ErisModel
    metrics: NormMetrics = field(default_factory=NormMetrics)
    _seed: int | None = None
    _pre_step_hooks: list[Callable[[Dict[str, Any], ActionInstance], None]] = field(
        default_factory=list
    )
    _post_step_hooks: list[
        Callable[[Dict[str, Any], ActionInstance, Dict[str, Any]], None]
    ] = field(default_factory=list)

    def reset(self, seed: int | None = None) -> Dict[str, Any]:
        """
        Reset the engine state and metrics.

        Args:
            seed: Optional random seed for reproducibility.

        Returns:
            Initial state (currently empty/undefined in base model,
            so returns empty dict or model's initial state if available).
        """
        self._seed = seed
        self.metrics = NormMetrics()
        # Future: self.model.env.reset(seed) if environment supports it
        return {}

    def register_pre_step_hook(
        self, hook: Callable[[Dict[str, Any], ActionInstance], None]
    ) -> None:
        """Register a callback to run before each step."""
        self._pre_step_hooks.append(hook)

    def register_post_step_hook(
        self,
        hook: Callable[[Dict[str, Any], ActionInstance, Dict[str, Any]], None],
    ) -> None:
        """Register a callback to run after each step."""
        self._post_step_hooks.append(hook)

    def step(self, state: Dict[str, Any], action: ActionInstance) -> Dict[str, Any]:
        """
        Execute one simulation step.

        1. Run pre-step hooks.
        2. Check norm prohibitions.
        3. Execute environment rule.
        4. Run post-step hooks.
        5. Return new state.
        """
        # 1. Pre-step hooks
        for hook in self._pre_step_hooks:
            hook(state, action)

        self.metrics.steps += 1

        # 2. Norm enforcement
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

        # 3. Environment dynamics
        env = self.model.env
        if action.name not in env.rules:
            raise KeyError(f"No environment rule for action '{action.name}'")

        rule = env.rules[action.name]
        new_state = rule.update_fn(state, action.params)

        # 4. Post-step hooks
        for hook in self._post_step_hooks:
            hook(state, action, new_state)

        return new_state

    def close(self) -> None:
        """Cleanup resources."""
        pass
