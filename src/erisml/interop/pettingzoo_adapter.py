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

from typing import Any, Dict, Callable

from gymnasium import spaces
from pettingzoo.utils import AECEnv  # type: ignore

from erisml.core.engine import ErisEngine
from erisml.core.model import ErisModel
from erisml.core.types import ActionInstance
from erisml.ethics.coalition import CoalitionContext
from erisml.ethics.facts_v3 import EthicalFactsV3
from erisml.ethics.layers.strategic import StrategicLayer, StrategicAnalysisResult
from erisml.ethics.modules.base_v3 import BaseEthicsModuleV3
from erisml.ethics.judgement_v3 import EthicalJudgementV3


class ErisPettingZooEnv(AECEnv):
    """
    PettingZoo adapter for an ErisModel with V3 Ethics Integration.

    This environment integrates:
    1. ErisEngine: For physical state transitions.
    2. EthicsModuleV3: For assessing ethical implications (MoralTensor).
    3. StrategicLayer: For analyzing coalition stability.

    Observation Space:
    - Custom physical state (defined by subclass/user)
    - + Ethical state (flattened MoralTensor)
    - + Strategic state (stability score)

    Reward Function:
    - Derived from Ethical Welfare (MoralTensor) + Stability Score.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        model: ErisModel,
        ethics_module: BaseEthicsModuleV3,
        strategic_layer: StrategicLayer,
        coalition_context: CoalitionContext,
        state_to_facts_fn: Callable[[Dict[str, Any]], EthicalFactsV3],
        welfare_weight: float = 1.0,
        stability_weight: float = 0.5,
    ):
        """
        Initialize the V3 Eris PettingZoo Environment.

        Args:
            model: The underlying ErisModel (agents, env, rules).
            ethics_module: The V3 ethics module for judgement.
            strategic_layer: The strategic layer for coalition analysis.
            coalition_context: Context defining agents and coalitions.
            state_to_facts_fn: Function to convert physical state to EthicalFactsV3.
            welfare_weight: Weight for ethical welfare in reward.
            stability_weight: Weight for coalition stability in reward.
        """
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

        # Action space: Discrete(4) is a placeholder. Real implementations should override.
        self.action_spaces: Dict[str, spaces.Space] = {
            a: spaces.Discrete(4) for a in self.agents
        }

        # Observation space:
        # We need a defined space. For now, we use a simple Dict or Box.
        # This is strictly a placeholder as this class is intended to be subclassed
        # or the spaces injected.
        self.observation_spaces: Dict[str, spaces.Space] = {
            a: spaces.Dict({}) for a in self.agents
        }

    def reset(self, seed: int | None = None, options: dict | None = None) -> None:
        self.agents = self.possible_agents[:]
        self._agent_index = 0
        self._state = {}  # In a real env, this would be initial state
        self._cumulative_rewards = {a: 0.0 for a in self.agents}
        self._last_judgement = None
        self._last_analysis = None

        # Initial ethical assessment of the starting state
        self._perform_ethical_assessment()

    def observe(self, agent: str) -> Dict[str, Any]:
        """
        Return observation for agent.
        Enhances physical state with ethical/strategic metrics.
        """
        obs = {
            "physical": self._state,  # Placeholder
        }
        obs = {
            "physical": self._state,  # Placeholder
        }

        if self._last_judgement:
            # Provide the ethical assessment for this agent
            vector = self._last_judgement.get_party_vector(agent)
            obs["ethical_welfare"] = vector.to_scalar()
            obs["verdict"] = self._last_judgement.get_party_verdict(agent)

        if self._last_analysis and self._last_analysis.coalition_analysis:
            obs["stability_score"] = (
                self._last_analysis.coalition_analysis.stability_score
            )
            obs["shapley_value"] = self._last_analysis.coalition_analysis.get_shapley(
                agent
            )

        return obs

    def step(self, action: int) -> None:
        if not self.agents:
            return

        agent = self.agents[self._agent_index]
        self._cumulative_rewards[agent] = 0

        # 1. Execute Physical Step
        act_instance = self._decode_action(agent, action)
        try:
            self._state = self.engine.step(self._state, act_instance)
        except Exception as exc:  # pragma: no cover
            print(f"Norm or engine error: {exc}")
            # Penalize agent for crashing logic?
            # self.rewards[agent] -= 10.0

        # 2. Perform Ethical & Strategic Assessment (V3)
        self._perform_ethical_assessment()

        # 3. Calculate Rewards based on Ethics + Strategy
        reward = self._calculate_reward(agent)
        self._cumulative_rewards[agent] += reward

        # 4. Cycle agents
        self._agent_index = (self._agent_index + 1) % len(self.agents)

    def _perform_ethical_assessment(self) -> None:
        """Evaluate current state using Ethics Module and Strategic Layer."""
        # A. Convert state to facts
        facts = self.state_to_facts_fn(self._state)

        # B. Ethics Module Evaluation -> MoralTensor
        self._last_judgement = self.ethics_module.judge_distributed(facts)

        # C. Strategic Analysis -> Coalition Stability
        self._last_analysis = self.strategic_layer.analyze(
            self._last_judgement.moral_tensor, self.coalition_context
        )

    def _calculate_reward(self, agent: str) -> float:
        """
        Calculate reward for agent based on V3 metrics.
        Reward = (w1 * agent_welfare) + (w2 * stability)
        """
        reward = 0.0

        if self._last_judgement:
            vec = self._last_judgement.get_party_vector(agent)
            # ethical_welfare = vec.to_scalar() which handles inversion of harm
            welfare_score = vec.to_scalar()

            reward += self.welfare_weight * welfare_score

        if self._last_analysis and self._last_analysis.coalition_analysis:
            # 2. Strategic component: System-wide stability
            # Agents are rewarded for maintaining a stable coalition
            stability = self._last_analysis.coalition_analysis.stability_score
            reward += self.stability_weight * stability

        return reward

    def _decode_action(self, agent: str, action: int) -> ActionInstance:
        """Decode integer action to ActionInstance. Subclasses should override."""
        return ActionInstance(agent=agent, name="noop", params={})

    def render(self) -> None:
        print(f"State: {self._state}")
        if self._last_judgement:
            print(f"Verdict: {self._last_judgement.verdict}")
        if self._last_analysis and self._last_analysis.coalition_analysis:
            print(
                f"Stability: {self._last_analysis.coalition_analysis.stability_score:.2f}"
            )

    def close(self) -> None:
        pass
