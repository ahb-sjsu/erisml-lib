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

from typing import Any, Dict

from gymnasium import spaces
from pettingzoo.utils import AECEnv  # type: ignore[import-untyped]

from erisml.core.engine import ErisEngine
from erisml.core.model import ErisModel
from erisml.core.types import ActionInstance


class ErisPettingZooEnv(AECEnv):
    """Minimal PettingZoo adapter for an ErisModel.

    This is a stub: you must customize observation and action spaces for
    your particular domain. The purpose here is to show how ErisEngine
    can be embedded behind the PettingZoo API.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(self, model: ErisModel):
        super().__init__()
        self.model = model
        self.engine = ErisEngine(model)
        self.possible_agents = list(model.agents.keys())
        self.agents = self.possible_agents[:]
        self._agent_index = 0
        self._state: Dict[str, Any] = {}
        self._cumulative_rewards = {a: 0.0 for a in self.agents}

        self.action_spaces: Dict[str, spaces.Space[Any]] = {
            a: spaces.Discrete(4) for a in self.agents
        }
        self.observation_spaces: Dict[str, spaces.Space[Any]] = {
            a: spaces.Dict({}) for a in self.agents
        }

    def reset(self, seed: int | None = None, options: dict | None = None) -> None:
        self.agents = self.possible_agents[:]
        self._agent_index = 0
        self._state = {}
        self._cumulative_rewards = {a: 0.0 for a in self.agents}

    def observe(self, agent: str) -> Dict[str, Any]:
        return {}

    def step(self, action: int) -> None:
        if not self.agents:
            return
        agent = self.agents[self._agent_index]
        act = self._decode_action(agent, action)
        try:
            self._state = self.engine.step(self._state, act)
        except Exception as exc:  # pragma: no cover - demo behavior
            print(f"Norm or engine error: {exc}")
        self._agent_index = (self._agent_index + 1) % len(self.agents)

    def _decode_action(self, agent: str, action: int) -> ActionInstance:
        return ActionInstance(agent=agent, name="noop", params={})

    def render(self) -> None:
        print("State:", self._state)

    def close(self) -> None:
        pass
