"""
Strategic Layer: Game Theoretic Analysis for ErisML
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict
import itertools
import numpy as np


@dataclass
class NashResult:
    equilibrium_profiles: List[Tuple[int, ...]]
    is_unique: bool


class StrategicLayer:
    """
    Analyzes payoffs to find stable Nash Equilibria.
    """

    def solve_nash(
        self, payoff_tensor: np.ndarray, agents: List[str], actions: List[str]
    ) -> NashResult:
        n_agents = len(agents)
        n_actions = len(actions)

        # Generate all possible strategy profiles
        action_ranges = [range(n_actions) for _ in range(n_agents)]
        profiles = list(itertools.product(*action_ranges))

        equilibria = []

        print(
            f"⚙️  Solving Game Matrix: {n_agents} Agents, {n_actions} Actions ({len(profiles)} outcomes)"
        )

        for profile in profiles:
            if self._is_stable(profile, payoff_tensor, n_agents, n_actions):
                equilibria.append(profile)

        return NashResult(
            equilibrium_profiles=equilibria, is_unique=(len(equilibria) == 1)
        )

    def _is_stable(
        self,
        profile: Tuple[int, ...],
        payoffs: np.ndarray,
        n_agents: int,
        n_actions: int,
    ) -> bool:
        # Check if any agent wants to deviate
        for agent_idx in range(n_agents):
            current_action = profile[agent_idx]
            current_utility = payoffs[(agent_idx,) + profile]

            for other_action in range(n_actions):
                if other_action == current_action:
                    continue

                # Hypothesize switching action
                hypothetical_profile = list(profile)
                hypothetical_profile[agent_idx] = other_action
                hypothetical_profile = tuple(hypothetical_profile)

                hypothetical_utility = payoffs[(agent_idx,) + hypothetical_profile]

                if hypothetical_utility > current_utility:
                    return False  # Unstable: Agent improves by switching

        return True
