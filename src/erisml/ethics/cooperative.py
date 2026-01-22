"""
Cooperative Game Theory Layer: Shapley Values & Coalition Analysis
"""

import itertools
import math
from typing import Dict, List, Callable


class CooperativeLayer:
    """
    Analyzes coalitional stability and fair credit assignment (Shapley Values).
    """

    def calculate_shapley_values(
        self, agents: List[str], characteristic_function: Callable[[List[str]], float]
    ) -> Dict[str, float]:
        n = len(agents)
        shapley_values = {agent: 0.0 for agent in agents}
        factorial_n = math.factorial(n)

        print(f"⚙️  Calculating Shapley Values for {n} agents...")

        for permutation in itertools.permutations(agents):
            current_coalition = []
            previous_value = 0.0

            for agent in permutation:
                current_coalition.append(agent)
                current_value = characteristic_function(current_coalition)
                marginal_contribution = current_value - previous_value
                shapley_values[agent] += marginal_contribution
                previous_value = current_value

        for agent in agents:
            shapley_values[agent] /= factorial_n

        return shapley_values

    def analyze_coalition_stability(
        self, shapley_values: Dict[str, float], total_group_value: float
    ) -> bool:
        total_distributed = sum(shapley_values.values())
        return math.isclose(total_distributed, total_group_value, rel_tol=1e-5)
