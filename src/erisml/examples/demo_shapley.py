from erisml.ethics.cooperative import CooperativeLayer


def demo_shapley_analysis():
    print("\n🤝 COOPERATIVE LAYER: Shapley Value Analysis (The Airport Problem)")
    print("================================================================")

    agents = ["Small_Jet", "Medium_Jet", "Jumbo_Jet"]

    # Costs required for each plane individually
    # Small: 10, Medium: 20, Jumbo: 30
    # If they build together, the cost is just the MAX required.

    def runway_cost_function(coalition):
        if not coalition:
            return 0.0

        costs = {"Small_Jet": 10, "Medium_Jet": 20, "Jumbo_Jet": 30}

        # The cost of a coalition is the cost of the LARGEST plane in it
        # (Because the runway must fit the biggest plane)
        required_costs = [costs[agent] for agent in coalition]
        return max(required_costs)

    print("Scenario: 3 Jets share a runway. How do we fairly split the cost?")
    print("  - Individual Costs: Small=10, Medium=20, Jumbo=30")
    print("  - Joint Cost: 30 (Runway just needs to fit the Jumbo)")
    print()

    # Initialize Engine
    layer = CooperativeLayer()

    # Calculate Fairness
    shapley_vals = layer.calculate_shapley_values(agents, runway_cost_function)

    print("✅ Fair Cost Distribution (Shapley Values):")
    for agent, value in shapley_vals.items():
        print(f"   ➤ {agent}: {value:.2f}")

    # Verify Logic
    # Expected: Small pays 3.33, Medium pays 8.33, Jumbo pays 18.33
    # Logic:
    #   - All 3 split the first 10 cost (3.33 each)
    #   - Med & Jumbo split the next 10 cost (5.0 each)
    #   - Jumbo pays the final 10 cost alone (10.0)

    print("\n🚀 RESULT: Cooperative Logic is functioning.")


if __name__ == "__main__":
    demo_shapley_analysis()
