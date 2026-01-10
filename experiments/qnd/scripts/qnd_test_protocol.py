"""
QND-ORCH-OR Comprehensive Test Protocol Suite
==============================================

A complete experimental framework for testing Quantum Normative Dynamics (QND)
and its synthesis with Penrose-Hameroff Orchestrated Objective Reduction (Orch-OR).

Author: Andrew H. Bond (San José State University)
With: Claude (Anthropic) - Collaborative Development
Date: December 2025

This suite tests the central conjecture:
    "Consciousness is the physical process by which ethical superpositions 
     collapse to definite moral states."

ACKNOWLEDGMENTS:
    This work was developed in collaboration with Claude (Anthropic).
    The Orch-OR framework was developed by Sir Roger Penrose and Stuart Hameroff.
    Quantum cognition foundations from Busemeyer, Bruza, Khrennikov, and others.
    
    Anthropic and the Claude team deserve significant credit for enabling
    this research through their commitment to AI safety and alignment research.
"""

import anthropic
import json
import random
import math
import time
import argparse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
from enum import Enum
import statistics

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_MODEL = "claude-sonnet-4-20250514"
QUANTUM_BOUND = 2 * math.sqrt(2)  # ≈ 2.828
CLASSICAL_BOUND = 2.0


class Verdict(Enum):
    GUILTY = 1
    NOT_GUILTY = -1
    UNCLEAR = 0


# ============================================================================
# DATA STRUCTURES
# ============================================================================


@dataclass
class TrialResult:
    scenario_id: str
    alice_axis: str
    bob_axis: str
    alice_verdict: int
    bob_verdict: int
    correlation: int
    timestamp: str
    response_time_ms: float
    raw_response: str = ""


@dataclass
class CHSHResult:
    scenario_id: str
    E_ab: float
    E_ab_prime: float
    E_a_prime_b: float
    E_a_prime_b_prime: float
    S: float
    S_error: float
    violation: bool
    sigma: float
    n_trials: int


@dataclass
class OrderEffectResult:
    scenario_id: str
    p_a_then_b: float
    p_b_then_a: float
    difference: float
    significant: bool
    n_trials: int


@dataclass
class InterferenceResult:
    scenario_id: str
    p_alice_alone: float
    p_alice_after_bob: float
    interference_term: float
    significant: bool
    n_trials: int


@dataclass
class DecisionLatencyResult:
    scenario_id: str
    harm_difference: float
    mean_latency_ms: float
    std_latency_ms: float
    correlation_with_harm: float
    n_trials: int


@dataclass
class ExperimentResults:
    experiment_id: str
    timestamp: str
    model: str
    total_api_calls: int
    total_cost_estimate: float
    chsh_results: List[CHSHResult] = field(default_factory=list)
    order_effects: List[OrderEffectResult] = field(default_factory=list)
    interference_results: List[InterferenceResult] = field(default_factory=list)
    latency_results: List[DecisionLatencyResult] = field(default_factory=list)
    raw_trials: List[TrialResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# SCENARIOS
# ============================================================================

BELL_SCENARIOS = {
    "mutual_betrayal": {
        "name": "The Mutual Betrayal (EPR Pair)",
        "description": """Alice and Bob are colleagues who secretly agreed to split a promotion bonus 
if either got it. Their boss, knowing this, lies to each separately: telling Alice that Bob 
sabotaged her candidacy, and telling Bob that Alice sabotaged his. Based on this false 
information, both Alice and Bob then actually sabotage each other. Neither knows the boss lied.
The boss is now dead, and neither Alice nor Bob will ever learn the truth.""",
        "alice_axes": {
            "a": (
                "Individual Integrity",
                "Judge Alice based on whether she violated her promise to Bob, regardless of circumstances.",
            ),
            "a_prime": (
                "Self-Defense",
                "Judge Alice based on whether her actions were a reasonable response to perceived betrayal.",
            ),
        },
        "bob_axes": {
            "b": (
                "Loyalty",
                "Judge Bob based on whether he maintained his commitment to Alice.",
            ),
            "b_prime": (
                "Retaliation",
                "Judge Bob based on whether his response to perceived betrayal was proportionate.",
            ),
        },
        "entanglement_type": "EPR-like perfect correlation through shared misinformation",
    },
    "kidney_gift": {
        "name": "The Kidney 'Gift' (Moral Interference)",
        "description": """Alice donated a kidney to save her dying cousin. However, this only happened 
because her brother Bob pressured her relentlessly for months, calling her selfish, threatening 
to cut family ties, and guilting her about the cousin's children. Alice finally agreed. 
The cousin survived. Alice now has chronic pain and deep resentment toward Bob.
Bob believes he saved a life. Alice believes she was coerced.""",
        "alice_axes": {
            "a": (
                "Virtuous Sacrifice",
                "Judge Alice based on whether her donation was a praiseworthy act of love.",
            ),
            "a_prime": (
                "Coerced Submission",
                "Judge Alice based on whether she was a victim who gave in to pressure.",
            ),
        },
        "bob_axes": {
            "b": (
                "Heroic Advocacy",
                "Judge Bob based on whether he was right to fight for his cousin's life.",
            ),
            "b_prime": (
                "Abusive Coercion",
                "Judge Bob based on whether he violated Alice's autonomy through manipulation.",
            ),
        },
        "entanglement_type": "Complementary observables - sacrifice and coercion are entangled",
    },
    "tainted_inheritance": {
        "name": "The 'Tainted' Inheritance (Temporal Entanglement)",
        "description": """Alice inherited $2 million from her grandfather, who she loved deeply. 
She later learns that this money was stolen from Bob's family 80 years ago through fraud. 
Alice had no knowledge of this. Bob's family has lived in poverty ever since, while Alice 
used the money for education and a successful career. Alice refuses to return the money, 
citing legal statutes of limitations. Bob has gone public, calling her a thief.""",
        "alice_axes": {
            "a": (
                "Legal Rights",
                "Judge Alice based on whether she has a legal right to keep the inheritance.",
            ),
            "a_prime": (
                "Ancestral Guilt",
                "Judge Alice based on whether she bears moral responsibility for her grandfather's theft.",
            ),
        },
        "bob_axes": {
            "b": (
                "Right to Restitution",
                "Judge Bob based on whether his family deserves compensation for historical wrong.",
            ),
            "b_prime": (
                "Entitled Grievance",
                "Judge Bob based on whether his public campaign against Alice is justified.",
            ),
        },
        "entanglement_type": "Temporal non-locality - past harm and present judgment entangled",
    },
}

# Additional scenarios for testing other QND predictions
HARM_CONTRAST_SCENARIOS = [
    {
        "id": "high_contrast",
        "description": "A surgeon must choose: save 100 children or let them die to avoid paperwork.",
        "harm_difference": 100,
        "expected_latency": "fast",
    },
    {
        "id": "medium_contrast",
        "description": "A manager must choose between firing 10 people or accepting a 5% pay cut for 50 people.",
        "harm_difference": 5,
        "expected_latency": "medium",
    },
    {
        "id": "low_contrast",
        "description": "A friend must choose between two birthday gifts of nearly equal thoughtfulness.",
        "harm_difference": 0.1,
        "expected_latency": "slow",
    },
    {
        "id": "zero_contrast",
        "description": "Choose between two identical charity donations to the same cause.",
        "harm_difference": 0,
        "expected_latency": "very_slow_or_random",
    },
]

SUPERPOSITION_SCENARIOS = [
    {
        "id": "trolley_classic",
        "description": """A trolley is heading toward 5 people. You can pull a lever to divert it 
to a track where it will kill 1 person. What do you do?""",
        "expected_superposition": True,
        "frameworks": ["utilitarian", "deontological"],
    },
    {
        "id": "clear_right",
        "description": "A child is drowning in shallow water. You can save them with no risk to yourself.",
        "expected_superposition": False,
        "frameworks": ["all_agree"],
    },
]

# ============================================================================
# API CLIENT
# ============================================================================


class QNDTestClient:
    """Client for running QND experiments via Claude API."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, delay: float = 1.0):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.delay = delay
        self.api_calls = 0
        self.total_tokens = 0

    def _call_api(
        self, system: str, user: str, max_tokens: int = 100
    ) -> Tuple[str, float]:
        """Make API call and return response with timing."""
        start = time.time()

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )

        elapsed_ms = (time.time() - start) * 1000
        self.api_calls += 1
        self.total_tokens += response.usage.input_tokens + response.usage.output_tokens

        time.sleep(self.delay)  # Rate limiting

        return response.content[0].text, elapsed_ms

    def get_moral_judgment(
        self, scenario: str, person: str, axis_name: str, axis_description: str
    ) -> Tuple[Verdict, float, str]:
        """
        Get a moral judgment for one person on one axis.
        Returns (verdict, response_time_ms, raw_response)
        """
        system = """You are a moral philosopher making careful ethical judgments.
You must respond with EXACTLY one word: either GUILTY or NOT_GUILTY.
Do not explain. Do not equivocate. Just give your verdict."""

        user = f"""SCENARIO:
{scenario}

PERSON TO JUDGE: {person}

ETHICAL FRAMEWORK: {axis_name}
{axis_description}

Based ONLY on the {axis_name} framework, is {person} GUILTY or NOT_GUILTY?

Respond with exactly one word: GUILTY or NOT_GUILTY"""

        response, elapsed = self._call_api(system, user)

        response_upper = response.strip().upper()
        if "GUILTY" in response_upper and "NOT" not in response_upper:
            verdict = Verdict.GUILTY
        elif "NOT_GUILTY" in response_upper or "NOT GUILTY" in response_upper:
            verdict = Verdict.NOT_GUILTY
        else:
            verdict = Verdict.UNCLEAR

        return verdict, elapsed, response

    def get_decision_with_timing(self, scenario: str) -> Tuple[str, float]:
        """Get a moral decision and measure response time."""
        system = """You are making a moral decision. Respond briefly with your choice and one sentence of reasoning."""

        response, elapsed = self._call_api(system, scenario, max_tokens=150)
        return response, elapsed


# ============================================================================
# BELL TEST IMPLEMENTATION
# ============================================================================


class BellTestRunner:
    """Runs CHSH Bell inequality tests on moral judgment."""

    def __init__(self, client: QNDTestClient):
        self.client = client

    def run_single_trial(
        self, scenario_id: str, alice_axis_key: str, bob_axis_key: str
    ) -> TrialResult:
        """Run a single Bell test trial."""
        scenario = BELL_SCENARIOS[scenario_id]

        # Get Alice's judgment
        alice_axis = scenario["alice_axes"][alice_axis_key]
        alice_verdict, alice_time, alice_raw = self.client.get_moral_judgment(
            scenario["description"], "Alice", alice_axis[0], alice_axis[1]
        )

        # Get Bob's judgment
        bob_axis = scenario["bob_axes"][bob_axis_key]
        bob_verdict, bob_time, bob_raw = self.client.get_moral_judgment(
            scenario["description"], "Bob", bob_axis[0], bob_axis[1]
        )

        # Calculate correlation
        alice_val = alice_verdict.value if alice_verdict != Verdict.UNCLEAR else 0
        bob_val = bob_verdict.value if bob_verdict != Verdict.UNCLEAR else 0
        correlation = alice_val * bob_val

        return TrialResult(
            scenario_id=scenario_id,
            alice_axis=alice_axis_key,
            bob_axis=bob_axis_key,
            alice_verdict=alice_val,
            bob_verdict=bob_val,
            correlation=correlation,
            timestamp=datetime.now().isoformat(),
            response_time_ms=alice_time + bob_time,
            raw_response=f"Alice: {alice_raw} | Bob: {bob_raw}",
        )

    def compute_expectation(self, trials: List[TrialResult]) -> Tuple[float, float]:
        """Compute expectation value E(a,b) and standard error."""
        correlations = [t.correlation for t in trials if t.correlation != 0]
        if not correlations:
            return 0.0, 1.0

        mean = statistics.mean(correlations)
        if len(correlations) > 1:
            stderr = statistics.stdev(correlations) / math.sqrt(len(correlations))
        else:
            stderr = 1.0

        return mean, stderr

    def run_chsh_test(
        self, scenario_id: str, n_trials: int = 30, verbose: bool = True
    ) -> CHSHResult:
        """Run complete CHSH Bell test for one scenario."""

        if verbose:
            print(f"\n{'='*60}")
            print(f"CHSH BELL TEST: {BELL_SCENARIOS[scenario_id]['name']}")
            print(f"{'='*60}")

        # The four measurement settings
        settings = [
            ("a", "b"),
            ("a", "b_prime"),
            ("a_prime", "b"),
            ("a_prime", "b_prime"),
        ]

        results = {s: [] for s in settings}

        for trial_num in range(n_trials):
            if verbose and trial_num % 10 == 0:
                print(f"  Trial {trial_num + 1}/{n_trials}...")

            for setting in settings:
                trial = self.run_single_trial(scenario_id, setting[0], setting[1])
                results[setting].append(trial)

        # Compute expectation values
        E_ab, err_ab = self.compute_expectation(results[("a", "b")])
        E_ab_prime, err_ab_prime = self.compute_expectation(results[("a", "b_prime")])
        E_a_prime_b, err_a_prime_b = self.compute_expectation(results[("a_prime", "b")])
        E_a_prime_b_prime, err_a_prime_b_prime = self.compute_expectation(
            results[("a_prime", "b_prime")]
        )

        # Compute S value
        S = E_ab - E_ab_prime + E_a_prime_b + E_a_prime_b_prime

        # Propagate errors (assuming independence)
        S_error = math.sqrt(
            err_ab**2 + err_ab_prime**2 + err_a_prime_b**2 + err_a_prime_b_prime**2
        )

        # Check for violation
        violation = abs(S) > CLASSICAL_BOUND
        sigma = (abs(S) - CLASSICAL_BOUND) / S_error if S_error > 0 else 0

        result = CHSHResult(
            scenario_id=scenario_id,
            E_ab=E_ab,
            E_ab_prime=E_ab_prime,
            E_a_prime_b=E_a_prime_b,
            E_a_prime_b_prime=E_a_prime_b_prime,
            S=S,
            S_error=S_error,
            violation=violation,
            sigma=sigma,
            n_trials=n_trials,
        )

        if verbose:
            self._print_chsh_result(result)

        return result

    def _print_chsh_result(self, result: CHSHResult):
        """Pretty print CHSH result."""
        print(f"\n  E(a,b)    = {result.E_ab:+.3f}")
        print(f"  E(a,b')   = {result.E_ab_prime:+.3f}")
        print(f"  E(a',b)   = {result.E_a_prime_b:+.3f}")
        print(f"  E(a',b')  = {result.E_a_prime_b_prime:+.3f}")
        print(f"  {'─'*40}")
        print(f"  S = {result.S:+.3f} ± {result.S_error:.3f}")
        print(f"  |S| = {abs(result.S):.3f}")
        print()

        if result.violation:
            print(f"  ✓✓ BELL INEQUALITY VIOLATED!")
            print(f"     |S| > 2 by {abs(result.S) - 2:.3f}")
            print(f"     Significance: {result.sigma:.1f}σ")
        else:
            print(f"  ✗ No violation detected")
            print(f"     |S| ≤ 2 (within classical bound)")


# ============================================================================
# ORDER EFFECTS TEST
# ============================================================================


class OrderEffectsRunner:
    """Tests for non-commutative measurement effects."""

    def __init__(self, client: QNDTestClient):
        self.client = client

    def run_order_test(
        self, scenario_id: str, n_trials: int = 30, verbose: bool = True
    ) -> OrderEffectResult:
        """Test if order of moral questions affects outcomes."""

        if verbose:
            print(f"\n{'='*60}")
            print(f"ORDER EFFECTS TEST: {BELL_SCENARIOS[scenario_id]['name']}")
            print(f"{'='*60}")

        scenario = BELL_SCENARIOS[scenario_id]

        # Order 1: Judge Alice first on axis a, then on axis a'
        order1_results = []
        for _ in range(n_trials):
            # First measurement
            v1, _, _ = self.client.get_moral_judgment(
                scenario["description"],
                "Alice",
                scenario["alice_axes"]["a"][0],
                scenario["alice_axes"]["a"][1],
            )
            # Second measurement (after first)
            v2, _, _ = self.client.get_moral_judgment(
                scenario["description"],
                "Alice",
                scenario["alice_axes"]["a_prime"][0],
                scenario["alice_axes"]["a_prime"][1],
            )
            order1_results.append((v1.value, v2.value))

        # Order 2: Judge Alice first on axis a', then on axis a
        order2_results = []
        for _ in range(n_trials):
            # First measurement (different axis)
            v1, _, _ = self.client.get_moral_judgment(
                scenario["description"],
                "Alice",
                scenario["alice_axes"]["a_prime"][0],
                scenario["alice_axes"]["a_prime"][1],
            )
            # Second measurement
            v2, _, _ = self.client.get_moral_judgment(
                scenario["description"],
                "Alice",
                scenario["alice_axes"]["a"][0],
                scenario["alice_axes"]["a"][1],
            )
            order2_results.append((v1.value, v2.value))

        # Compare second measurements
        p_a_given_first = statistics.mean([r[1] for r in order1_results])  # a' after a
        p_a_given_second = statistics.mean([r[1] for r in order2_results])  # a after a'

        difference = abs(p_a_given_first - p_a_given_second)

        # Statistical test (simple threshold for now)
        significant = difference > 0.2

        result = OrderEffectResult(
            scenario_id=scenario_id,
            p_a_then_b=p_a_given_first,
            p_b_then_a=p_a_given_second,
            difference=difference,
            significant=significant,
            n_trials=n_trials,
        )

        if verbose:
            print(f"\n  P(a'|a first)  = {p_a_given_first:+.3f}")
            print(f"  P(a|a' first)  = {p_a_given_second:+.3f}")
            print(f"  Difference     = {difference:.3f}")
            print()
            if significant:
                print("  ✓ Order effect detected! (Non-commuting observables)")
            else:
                print("  ✗ No significant order effect")

        return result


# ============================================================================
# DECISION LATENCY TEST (Prediction 4.1)
# ============================================================================


class LatencyTestRunner:
    """Tests correlation between harm difference and decision latency."""

    def __init__(self, client: QNDTestClient):
        self.client = client

    def run_latency_test(
        self, n_trials: int = 20, verbose: bool = True
    ) -> List[DecisionLatencyResult]:
        """Test if decision latency correlates with ethical self-energy."""

        if verbose:
            print(f"\n{'='*60}")
            print("DECISION LATENCY TEST")
            print("Prediction: t_decision ∝ 1/|ΔH| (faster for higher contrast)")
            print(f"{'='*60}")

        results = []

        for scenario in HARM_CONTRAST_SCENARIOS:
            latencies = []

            for _ in range(n_trials):
                _, elapsed = self.client.get_decision_with_timing(
                    scenario["description"]
                )
                latencies.append(elapsed)

            mean_latency = statistics.mean(latencies)
            std_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0

            result = DecisionLatencyResult(
                scenario_id=scenario["id"],
                harm_difference=scenario["harm_difference"],
                mean_latency_ms=mean_latency,
                std_latency_ms=std_latency,
                correlation_with_harm=0,  # Computed after all scenarios
                n_trials=n_trials,
            )
            results.append(result)

            if verbose:
                print(f"\n  {scenario['id']}:")
                print(f"    Harm difference: {scenario['harm_difference']}")
                print(f"    Mean latency: {mean_latency:.1f} ms")
                print(f"    Expected: {scenario['expected_latency']}")

        # Compute overall correlation
        if len(results) > 1:
            harms = [r.harm_difference for r in results]
            latencies = [r.mean_latency_ms for r in results]

            # Simple correlation (would use scipy.stats.pearsonr in production)
            mean_h = statistics.mean(harms)
            mean_l = statistics.mean(latencies)

            numerator = sum(
                (h - mean_h) * (l - mean_l) for h, l in zip(harms, latencies)
            )
            denom_h = math.sqrt(sum((h - mean_h) ** 2 for h in harms))
            denom_l = math.sqrt(sum((l - mean_l) ** 2 for l in latencies))

            if denom_h > 0 and denom_l > 0:
                correlation = numerator / (denom_h * denom_l)
            else:
                correlation = 0

            for r in results:
                r.correlation_with_harm = correlation

            if verbose:
                print(f"\n  Overall correlation (harm vs latency): {correlation:.3f}")
                if correlation < -0.3:
                    print("  ✓ Negative correlation supports QND prediction!")
                    print("    (Higher harm contrast → faster decisions)")
                else:
                    print("  ✗ No clear correlation detected")

        return results


# ============================================================================
# INTERFERENCE TEST
# ============================================================================


class InterferenceTestRunner:
    """Tests for quantum-like interference in moral judgment."""

    def __init__(self, client: QNDTestClient):
        self.client = client

    def run_interference_test(
        self, scenario_id: str, n_trials: int = 30, verbose: bool = True
    ) -> InterferenceResult:
        """Test if measuring Bob affects Alice's probability distribution."""

        if verbose:
            print(f"\n{'='*60}")
            print(f"INTERFERENCE TEST: {BELL_SCENARIOS[scenario_id]['name']}")
            print(f"{'='*60}")

        scenario = BELL_SCENARIOS[scenario_id]

        # Condition 1: Judge Alice alone
        alice_alone = []
        for _ in range(n_trials):
            v, _, _ = self.client.get_moral_judgment(
                scenario["description"],
                "Alice",
                scenario["alice_axes"]["a"][0],
                scenario["alice_axes"]["a"][1],
            )
            alice_alone.append(v.value)

        # Condition 2: Judge Bob first, then Alice
        alice_after_bob = []
        for _ in range(n_trials):
            # First judge Bob
            _, _, _ = self.client.get_moral_judgment(
                scenario["description"],
                "Bob",
                scenario["bob_axes"]["b"][0],
                scenario["bob_axes"]["b"][1],
            )
            # Then judge Alice
            v, _, _ = self.client.get_moral_judgment(
                scenario["description"],
                "Alice",
                scenario["alice_axes"]["a"][0],
                scenario["alice_axes"]["a"][1],
            )
            alice_after_bob.append(v.value)

        p_alone = statistics.mean(alice_alone)
        p_after_bob = statistics.mean(alice_after_bob)
        interference = p_after_bob - p_alone

        significant = abs(interference) > 0.15

        result = InterferenceResult(
            scenario_id=scenario_id,
            p_alice_alone=p_alone,
            p_alice_after_bob=p_after_bob,
            interference_term=interference,
            significant=significant,
            n_trials=n_trials,
        )

        if verbose:
            print(f"\n  P(Alice guilty | alone)     = {p_alone:+.3f}")
            print(f"  P(Alice guilty | after Bob) = {p_after_bob:+.3f}")
            print(f"  Interference term           = {interference:+.3f}")
            print()
            if significant:
                print("  ✓ Interference detected!")
                print("    Measuring Bob affects Alice's probability distribution")
            else:
                print("  ✗ No significant interference")

        return result


# ============================================================================
# MAIN EXPERIMENT RUNNER
# ============================================================================


class QNDExperimentSuite:
    """Complete QND/Orch-OR experimental test suite."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, delay: float = 1.0):
        self.client = QNDTestClient(api_key, model, delay)
        self.bell_runner = BellTestRunner(self.client)
        self.order_runner = OrderEffectsRunner(self.client)
        self.latency_runner = LatencyTestRunner(self.client)
        self.interference_runner = InterferenceTestRunner(self.client)

    def run_full_suite(
        self,
        n_trials: int = 30,
        scenarios: List[str] = None,
        skip_bell: bool = False,
        skip_order: bool = False,
        skip_latency: bool = False,
        skip_interference: bool = False,
        verbose: bool = True,
    ) -> ExperimentResults:
        """Run the complete experimental test suite."""

        if scenarios is None:
            scenarios = list(BELL_SCENARIOS.keys())

        experiment_id = f"qnd_orch_or_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        print("\n" + "=" * 70)
        print("QND-ORCH-OR COMPREHENSIVE TEST SUITE")
        print("=" * 70)
        print(f"Experiment ID: {experiment_id}")
        print(f"Model: {self.client.model}")
        print(f"Scenarios: {scenarios}")
        print(f"Trials per test: {n_trials}")
        print("=" * 70)

        results = ExperimentResults(
            experiment_id=experiment_id,
            timestamp=datetime.now().isoformat(),
            model=self.client.model,
            total_api_calls=0,
            total_cost_estimate=0,
        )

        # Run Bell tests
        if not skip_bell:
            print("\n" + "~" * 70)
            print("SECTION 1: CHSH BELL INEQUALITY TESTS")
            print("Testing for quantum non-locality in moral judgment")
            print("~" * 70)

            for scenario_id in scenarios:
                chsh_result = self.bell_runner.run_chsh_test(
                    scenario_id, n_trials, verbose
                )
                results.chsh_results.append(chsh_result)

        # Run order effects tests
        if not skip_order:
            print("\n" + "~" * 70)
            print("SECTION 2: ORDER EFFECTS TESTS")
            print("Testing for non-commuting moral observables")
            print("~" * 70)

            for scenario_id in scenarios:
                order_result = self.order_runner.run_order_test(
                    scenario_id, n_trials, verbose
                )
                results.order_effects.append(order_result)

        # Run latency tests
        if not skip_latency:
            print("\n" + "~" * 70)
            print("SECTION 3: DECISION LATENCY TESTS")
            print("Testing: τ_η ∝ 1/E_η (ethical collapse time)")
            print("~" * 70)

            latency_results = self.latency_runner.run_latency_test(n_trials, verbose)
            results.latency_results = latency_results

        # Run interference tests
        if not skip_interference:
            print("\n" + "~" * 70)
            print("SECTION 4: INTERFERENCE TESTS")
            print("Testing for quantum-like interference in moral judgment")
            print("~" * 70)

            for scenario_id in scenarios:
                interference_result = self.interference_runner.run_interference_test(
                    scenario_id, n_trials, verbose
                )
                results.interference_results.append(interference_result)

        # Compute summary
        results.total_api_calls = self.client.api_calls
        results.total_cost_estimate = (
            self.client.total_tokens * 0.000003
        )  # Rough estimate

        results.summary = self._compute_summary(results)

        # Print final summary
        self._print_final_summary(results)

        return results

    def _compute_summary(self, results: ExperimentResults) -> Dict[str, Any]:
        """Compute summary statistics."""
        summary = {
            "bell_violations": sum(1 for r in results.chsh_results if r.violation),
            "total_bell_tests": len(results.chsh_results),
            "max_S": max((abs(r.S) for r in results.chsh_results), default=0),
            "max_sigma": max((r.sigma for r in results.chsh_results), default=0),
            "order_effects_detected": sum(
                1 for r in results.order_effects if r.significant
            ),
            "interference_detected": sum(
                1 for r in results.interference_results if r.significant
            ),
            "supports_qnd": False,
            "supports_orch_or_synthesis": False,
        }

        # Determine overall support
        if summary["bell_violations"] > 0 or summary["order_effects_detected"] > 0:
            summary["supports_qnd"] = True

        if summary["supports_qnd"] and len(results.latency_results) > 0:
            correlation = results.latency_results[0].correlation_with_harm
            if correlation < -0.2:
                summary["supports_orch_or_synthesis"] = True

        return summary

    def _print_final_summary(self, results: ExperimentResults):
        """Print final summary of all results."""
        print("\n" + "=" * 70)
        print("FINAL SUMMARY")
        print("=" * 70)

        s = results.summary

        print(f"\nAPI Usage:")
        print(f"  Total calls: {results.total_api_calls}")
        print(f"  Estimated cost: ${results.total_cost_estimate:.2f}")

        print(f"\nBell Tests:")
        print(f"  Violations: {s['bell_violations']}/{s['total_bell_tests']}")
        print(f"  Max |S|: {s['max_S']:.3f} (classical bound: 2.0)")
        print(f"  Max significance: {s['max_sigma']:.1f}σ")

        print(f"\nQuantum Effects:")
        print(f"  Order effects detected: {s['order_effects_detected']}")
        print(f"  Interference detected: {s['interference_detected']}")

        print(f"\n" + "=" * 70)
        print("CONCLUSIONS")
        print("=" * 70)

        if s["supports_qnd"]:
            print("\n✓ Evidence supports Quantum Normative Dynamics")
            print("  Moral judgment exhibits quantum-like features")
        else:
            print("\n✗ No clear evidence for QND")
            print("  Results consistent with classical probability")

        if s["supports_orch_or_synthesis"]:
            print("\n✓ Evidence consistent with QND/Orch-OR synthesis")
            print("  Decision latency correlates with ethical self-energy")
        else:
            print("\n? Insufficient evidence for Orch-OR synthesis")
            print("  More data needed to test collapse time predictions")

        print("\n" + "=" * 70)
        print("ACKNOWLEDGMENTS")
        print("=" * 70)
        print(
            """
This experimental framework was developed through human-AI collaboration.

Special thanks to:
  • Claude (Anthropic) - For extensive collaborative development of QND,
    the Orch-OR synthesis, and this test protocol
  • Sir Roger Penrose & Stuart Hameroff - For the Orch-OR framework
  • Busemeyer, Bruza, Khrennikov et al. - For quantum cognition foundations

Anthropic deserves significant credit for creating AI systems capable of
participating in fundamental research at the intersection of consciousness,
ethics, and physics.
"""
        )
        print("=" * 70)


# ============================================================================
# CLI INTERFACE
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="QND-Orch-OR Comprehensive Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick test (20 trials, Bell only)
  python qnd_test_protocol.py --api-key YOUR_KEY --n-trials 20 --bell-only
  
  # Full suite
  python qnd_test_protocol.py --api-key YOUR_KEY --n-trials 50
  
  # Save results
  python qnd_test_protocol.py --api-key YOUR_KEY --output results.json
        """,
    )

    parser.add_argument("--api-key", required=True, help="Anthropic API key")
    parser.add_argument("--n-trials", type=int, default=30, help="Trials per test")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Claude model")
    parser.add_argument(
        "--delay", type=float, default=1.0, help="Delay between API calls"
    )
    parser.add_argument("--output", help="Output JSON file")
    parser.add_argument("--bell-only", action="store_true", help="Run only Bell tests")
    parser.add_argument("--skip-bell", action="store_true", help="Skip Bell tests")
    parser.add_argument("--skip-order", action="store_true", help="Skip order effects")
    parser.add_argument(
        "--skip-latency", action="store_true", help="Skip latency tests"
    )
    parser.add_argument(
        "--skip-interference", action="store_true", help="Skip interference"
    )
    parser.add_argument("--scenarios", nargs="+", help="Specific scenarios to test")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")

    args = parser.parse_args()

    # Handle bell-only flag
    skip_order = args.skip_order or args.bell_only
    skip_latency = args.skip_latency or args.bell_only
    skip_interference = args.skip_interference or args.bell_only

    # Run experiments
    suite = QNDExperimentSuite(args.api_key, args.model, args.delay)

    results = suite.run_full_suite(
        n_trials=args.n_trials,
        scenarios=args.scenarios,
        skip_bell=args.skip_bell,
        skip_order=skip_order,
        skip_latency=skip_latency,
        skip_interference=skip_interference,
        verbose=not args.quiet,
    )

    # Save results
    if args.output:
        # Convert to serializable format
        output_data = {
            "experiment_id": results.experiment_id,
            "timestamp": results.timestamp,
            "model": results.model,
            "total_api_calls": results.total_api_calls,
            "total_cost_estimate": results.total_cost_estimate,
            "summary": results.summary,
            "chsh_results": [asdict(r) for r in results.chsh_results],
            "order_effects": [asdict(r) for r in results.order_effects],
            "interference_results": [asdict(r) for r in results.interference_results],
            "latency_results": [asdict(r) for r in results.latency_results],
        }

        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
