# Copyright (c) 2026 Andrew H. Bond
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tests for V3 PettingZoo Adapter.
"""

import unittest
from unittest.mock import MagicMock

from erisml.core.model import ErisModel, EnvironmentModel
from erisml.ethics.coalition import CoalitionContext
from erisml.ethics.judgement_v3 import EthicalJudgementV3
from erisml.ethics.layers.strategic import (
    StrategicLayer,
    StrategicAnalysisResult,
    CoalitionStabilityAnalysis,
)
from erisml.ethics.modules.base_v3 import BaseEthicsModuleV3
from erisml.ethics.moral_tensor import MoralTensor
from erisml.ethics.moral_vector import MoralVector
from erisml.interop.pettingzoo_adapter import ErisPettingZooEnv
from erisml.ethics.facts_v3 import EthicalFactsV3


class TestErisPettingZooEnvV3(unittest.TestCase):
    def setUp(self):
        # 1. Mock ErisModel
        self.mock_env_model = MagicMock(spec=EnvironmentModel)
        self.mock_env_model.rules = {}
        self.mock_model = MagicMock(spec=ErisModel)
        self.mock_model.env = self.mock_env_model
        # Two agents
        self.mock_model.agents = {"agent_0": MagicMock(), "agent_1": MagicMock()}

        # 2. Mock EthicsModule
        self.mock_ethics = MagicMock(spec=BaseEthicsModuleV3)
        # Setup specific return values if needed

        # 3. Mock StrategicLayer
        self.mock_strategic = MagicMock(spec=StrategicLayer)

        # 4. Context
        self.context = CoalitionContext(agent_ids=("agent_0", "agent_1"))

        # 5. Converter
        self.mock_converter = MagicMock(return_value=MagicMock(spec=EthicalFactsV3))

        self.env = ErisPettingZooEnv(
            model=self.mock_model,
            ethics_module=self.mock_ethics,
            strategic_layer=self.mock_strategic,
            coalition_context=self.context,
            state_to_facts_fn=self.mock_converter,
            welfare_weight=1.0,
            stability_weight=1.0,
        )

    def test_initialization(self):
        self.assertEqual(len(self.env.possible_agents), 2)
        self.assertEqual(self.env.agents, ["agent_0", "agent_1"])

    def test_reset_performs_assessment(self):
        self.env.reset()
        self.mock_converter.assert_called()
        self.mock_ethics.judge_distributed.assert_called()
        self.mock_strategic.analyze.assert_called()

    def test_step_calculates_rewards(self):
        # Setup mocks to return specific values

        # A. Judgement returning a vector with known scalar score
        # MoralVector(rights_respect=1.0) -> scalar ~1.0 (depending on weights)
        vec_0 = MoralVector(rights_respect=1.0, physical_harm=0.0)
        vec_1 = MoralVector(rights_respect=0.0, physical_harm=1.0)  # Bad

        mock_judgement = MagicMock(spec=EthicalJudgementV3)
        mock_judgement.get_party_vector.side_effect = lambda a: (
            vec_0 if a == "agent_0" else vec_1
        )
        mock_judgement.moral_tensor = MagicMock(spec=MoralTensor)

        self.mock_ethics.judge_distributed.return_value = mock_judgement

        # B. Strategic Analysis returning stability score
        mock_analysis = MagicMock(spec=StrategicAnalysisResult)
        mock_coalition_res = MagicMock(spec=CoalitionStabilityAnalysis)
        mock_coalition_res.stability_score = 0.5
        mock_analysis.coalition_analysis = mock_coalition_res

        self.mock_strategic.analyze.return_value = mock_analysis

        # Perform Reset
        self.env.reset()

        # Step agent_0
        self.env.step(0)  # action 0

        # Check Reward for agent_0
        # Reward = 1.0 * welfare + 1.0 * stability
        # Welfare(vec_0) should be high ~0.9ish (default weights)
        # Stability = 0.5

        # AECEnv accumulates rewards in _cumulative_rewards
        # But 'step' clears it for the current agent before adding.
        # Wait, AEC logic:
        # "Rewards are instantaneous. ... cumulative_rewards are the sum of rewards since the last time the agent stepped."
        # In strictly sequential AEC, step(agent) generates reward for that agent.

        reward_0 = self.env._cumulative_rewards["agent_0"]

        # Check calculation
        expected_welfare_0 = vec_0.to_scalar()
        expected_reward_0 = 1.0 * expected_welfare_0 + 1.0 * 0.5

        self.assertAlmostEqual(reward_0, expected_reward_0, places=4)

        # Check observe
        obs = self.env.observe("agent_0")
        self.assertIn("ethical_welfare", obs)
        self.assertAlmostEqual(obs["ethical_welfare"], expected_welfare_0)
        self.assertEqual(obs["stability_score"], 0.5)


if __name__ == "__main__":
    unittest.main()
