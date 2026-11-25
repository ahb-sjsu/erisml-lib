# ErisML is a modeling layer for governed, foundation-model-enabled agents
# Copyright (c) 2025 Andrew H. Bond
# Contact: agi.hpc@gmail.com
#
# Licensed under the MIT License. See LICENSE.txt at the root of this repository.

from __future__ import annotations

from typing import Any, Callable, Dict

from gymnasium import spaces
from pettingzoo.utils import AECEnv  # type: ignore

from erisml.core.engine import ErisEngine
from erisml.core.model import ErisModel
from erisml.core.types import ActionInstance
from erisml.ethics.coalition import CoalitionContext
from erisml.ethics.facts_v3 import EthicalFactsV3
from erisml.ethics.judgement_v3 import EthicalJudgementV3
from erisml.ethics.layers.strategic import StrategicAnalysisResult, StrategicLayer
from erisml.ethics.modules.base_v3 import BaseEthicsModuleV3


class ErisPettingZooEnv(AECEnv):
    """PettingZoo adapter for ErisModel with optional DEME V3 ethics integration."""

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        model: ErisModel,
        ethics_module: BaseEthicsModuleV3 | None = None,
        strategic_layer: StrategicLayer | None = None,
        coalition_context: CoalitionContext | None = None,
        state_to_facts_fn: Callable[[Dict[str, Any]], EthicalFactsV3] | None = None,
        welfare_weight: float = 1.0,
        stability_weight: float = 0.5,
    ):
        super().__init__()
        self.model = model
        self.engine = ErisEngine(model)

        self.ethics_module = ethics_module
        self.strategic_layer = strategic_layer
        self.coalition_context = coalition_context
        self.state_to_facts_fn = state_to_facts_fn
        self.welfare_weight = welfare_weight
        self.stability_weight = stability_weight

        self.possible_agents = list(model.agents.keys())
        self.agents = self.possible_agents[:]
        self._agent_index = 0
        self._state: Dict[str, Any] = {}
        self._cumulative_rewards = {a: 0.0 for a in self.agents}
        self._last_judgement: EthicalJudgementV3 | None = None
        self._last_analysis: StrategicAnalysisResult | None = None

        self.action_spaces: Dict[str, spaces.Space] = {
            a: spaces.Discrete(4) for a in self.agents
        }
        self.observation_spaces: Dict[str, spaces.Space] = {
            a: spaces.Dict({}) for a in self.agents
        }

    @property
    def _ethics_enabled(self) -> bool:
        return all(
            (
                self.ethics_module is not None,
                self.strategic_layer is not None,
                self.coalition_context is not None,
                self.state_to_facts_fn is not None,
            )
        )

    def reset(self, seed: int | None = None, options: dict | None = None) -> None:
        del seed, options
        self.agents = self.possible_agents[:]
        self._agent_index = 0
        self._state = {}
        self._cumulative_rewards = {a: 0.0 for a in self.agents}
        self._last_judgement = None
        self._last_analysis = None

        if self._ethics_enabled:
            self._perform_ethical_assessment()

    def action_space(self, agent: str):
        """Return the action space for a given agent."""
        return self.action_spaces[agent]

    def observation_space(self, agent: str):
        """Return the observation space for a given agent."""
        return self.observation_spaces[agent]

    def observe(self, agent: str) -> Dict[str, Any]:
        obs: Dict[str, Any] = {"physical": self._state}

        if self._last_judgement is not None:
            vector = self._last_judgement.get_party_vector(agent)
            obs["ethical_welfare"] = vector.to_scalar()
            obs["verdict"] = self._last_judgement.get_party_verdict(agent)

        if self._last_analysis is not None and self._last_analysis.coalition_analysis:
            coalition = self._last_analysis.coalition_analysis
            obs["stability_score"] = coalition.stability_score
            obs["shapley_value"] = coalition.get_shapley(agent)

        if not self._ethics_enabled:
            return {}

        return obs

    def step(self, action: int) -> None:
        if not self.agents:
            return

        agent = self.agents[self._agent_index]
        self._cumulative_rewards[agent] = 0.0

        act = self._decode_action(agent, action)
        try:
            self._state = self.engine.step(self._state, act)
        except Exception as exc:  # pragma: no cover - demo behavior
            print(f"Norm or engine error: {exc}")

        if self._ethics_enabled:
            self._perform_ethical_assessment()
            reward = self._calculate_reward(agent)
            self._cumulative_rewards[agent] += reward

        self._agent_index = (self._agent_index + 1) % len(self.agents)

    def _perform_ethical_assessment(self) -> None:
        if not self._ethics_enabled:
            return

        assert self.state_to_facts_fn is not None
        assert self.ethics_module is not None
        assert self.strategic_layer is not None
        assert self.coalition_context is not None

        facts = self.state_to_facts_fn(self._state)
        self._last_judgement = self.ethics_module.judge_distributed(facts)
        self._last_analysis = self.strategic_layer.analyze(
            self._last_judgement.moral_tensor,
            self.coalition_context,
        )

    def _calculate_reward(self, agent: str) -> float:
        reward = 0.0

        if self._last_judgement is not None:
            reward += (
                self.welfare_weight
                * self._last_judgement.get_party_vector(agent).to_scalar()
            )

        if self._last_analysis is not None and self._last_analysis.coalition_analysis:
            reward += (
                self.stability_weight
                * self._last_analysis.coalition_analysis.stability_score
            )

        return reward

    def _decode_action(self, agent: str, action: int) -> ActionInstance:
        env_rules = getattr(self.model.env, "rules", {})
        available_rules = list(env_rules.keys())
        if not available_rules:
            return ActionInstance(agent=agent, name="noop", params={})

        rule_name = available_rules[action % len(available_rules)]
        return ActionInstance(agent=agent, name=rule_name, params={})

    def render(self) -> None:
        print("State:", self._state)
        if self._last_judgement is not None:
            print(f"Verdict: {self._last_judgement.verdict}")
        if self._last_analysis is not None and self._last_analysis.coalition_analysis:
            print(
                f"Stability: {self._last_analysis.coalition_analysis.stability_score:.2f}"
            )

    def close(self) -> None:
        pass
