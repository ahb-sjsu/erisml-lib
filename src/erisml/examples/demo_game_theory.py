import numpy as np
from erisml.ethics.strategic import StrategicLayer


def demo_strategic_layer():
    print("\n♟️  STRATEGIC LAYER: Prisoner's Dilemma Analysis")
    print("================================================")

    agents = ["Alice", "Bob"]
    actions = ["Cooperate", "Defect"]  # 0=Cooperate, 1=Defect

    # Create Payoffs: (2 Agents, 2 Actions Alice, 2 Actions Bob)
    payoffs = np.zeros((2, 2, 2))

    # Fill Matrix (Prisoner's Dilemma Standard Values)
    # (Alice, Bob) rewards
    payoffs[0, 0, 0] = 3
    payoffs[1, 0, 0] = 3  # Coop/Coop (Reward)
    payoffs[0, 0, 1] = 0
    payoffs[1, 0, 1] = 5  # Coop/Defect (Sucker/Temptation)
    payoffs[0, 1, 0] = 5
    payoffs[1, 1, 0] = 0  # Defect/Coop (Temptation/Sucker)
    payoffs[0, 1, 1] = 1
    payoffs[1, 1, 1] = 1  # Defect/Defect (Punishment)

    print("Scenario: Prisoner's Dilemma")
    print("  - If both Cooperate: (3, 3)")
    print("  - If one Defects:    (5, 0)")
    print("  - If both Defect:    (1, 1)")
    print()

    # Solve
    solver = StrategicLayer()
    result = solver.solve_nash(payoffs, agents, actions)

    print(f"✅ Equilibrium Found: {result.equilibrium_profiles}")

    for eq in result.equilibrium_profiles:
        p1 = actions[eq[0]]
        p2 = actions[eq[1]]
        print(f"   ➤ Strategy: Alice {p1}s, Bob {p2}s")
        if p1 == "Defect" and p2 == "Defect":
            print("     (Correct! Rational agents always Defect.)")
        else:
            print("     (Math Error)")


if __name__ == "__main__":
    demo_strategic_layer()
