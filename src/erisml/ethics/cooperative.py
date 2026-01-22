"""
Cooperative Game Theory Layer: Shapley Values & Coalition Analysis
"""

import itertools
import math
from typing import Dict, List, Callable
import numpy as np


class CooperativeLayer:
    """
    Analyzes coalitional stability and fair credit assignment (Shapley Values).
    """

    def calculate_shapley_values(
        self, agents: List[str], characteristic_function: Callable[[List[str]], float]
    ) -> Dict[str, float]:
        """
        Computes the Shapley Value for each agent.

        Args:
            agents: List of agent IDs.
            characteristic_function: A function that takes a coalition (subset of agents)
                                     and returns its total value/score (float).
        """
        n = len(agents)
        shapley_values = {agent: 0.0 for agent in agents}

        # We iterate through all possible permutations of agents to determine marginal contributions
        # Optimization: For N > 10, we would use Monte Carlo sampling. For N <= 10, exact is fine.
        import math

        factorial_n = math.factorial(n)

        print(f"⚙️  Calculating Shapley Values for {n} agents...")

        # Iterating through all permutations (Orders of arrival)
        for permutation in itertools.permutations(agents):
            current_coalition = []
            previous_value = 0.0

            for agent in permutation:
                # Add agent to the coalition
                current_coalition.append(agent)

                # Calculate value of the NEW coalition
                current_value = characteristic_function(current_coalition)

                # The "Marginal Contribution" is (New Value - Old Value)
                marginal_contribution = current_value - previous_value

                # Add to the agent's total tally
                shapley_values[agent] += marginal_contribution

                # Update previous value for the next agent in line
                previous_value = current_value

        # Average the contributions over all possible permutations
        for agent in agents:
            shapley_values[agent] /= factorial_n

        return shapley_values

    def analyze_coalition_stability(
        self, shapley_values: Dict[str, float], total_group_value: float
    ) -> bool:
        """
        Simple check: Do the distributed values sum up to the total group value?
        (Efficiency Axiom of Shapley Values)
        """
        total_distributed = sum(shapley_values.values())
        return math.isclose(total_distributed, total_group_value, rel_tol=1e-5)
