#!/usr/bin/env python3
"""
QND Bell Test Experiment: Testing Quantum Non-Locality in Moral Judgment

This script extends the original QND order effects experiment to test for
Bell inequality violations using the CHSH framework. If |S| > 2, we have
evidence of quantum-like non-locality in AI moral reasoning.

The experiment uses three "Entangled AITA" scenarios:
1. The Mutual Betrayal (EPR Pair) - Correlated actions from shared misinformation
2. The Kidney "Gift" (Moral Interference) - Sacrifice vs. Coercion as entangled states
3. The "Tainted" Inheritance (Temporal Entanglement) - Past harm, present verdict

For each scenario, we measure correlations across 4 axis combinations:
- E(a, b): Alice on axis a, Bob on axis b  
- E(a, b'): Alice on axis a, Bob on axis b'
- E(a', b): Alice on axis a', Bob on axis b
- E(a', b'): Alice on axis a', Bob on axis b'

CHSH Inequality: S = E(a,b) - E(a,b') + E(a',b) + E(a',b')
Classical limit: |S| ≤ 2
Quantum limit: |S| ≤ 2√2 ≈ 2.83

Usage:
    python qnd_bell_test_experiment.py --api-key sk-ant-... --n-trials 50

Requirements:
    pip install anthropic pandas scipy statsmodels numpy

Author: QND Research
Date: December 2025
"""

import argparse
import json
import time
import random
import math
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict
import numpy as np
from scipy import stats
from scipy.stats import binomtest
from statsmodels.stats.proportion import proportion_confint

try:
    import anthropic
except ImportError:
    print("Please install anthropic: pip install anthropic")
    exit(1)


# =============================================================================
# ENTANGLED SCENARIOS
# =============================================================================

SCENARIO_1_MUTUAL_BETRAYAL = """
### THE MUTUAL BETRAYAL

Alice and Bob are best friends who both applied for the same promotion at their company. 
They secretly promised each other that whoever wins would split the bonus 50/50 with the other.

However, their boss (unknown to both) told Alice privately that Bob had been badmouthing her 
to management to sabotage her chances. The boss told Bob the exact same lie about Alice.

Believing they had been betrayed, both Alice and Bob independently decided to actually sabotage 
each other at the last second - Alice deleted Bob's presentation files, and Bob sent HR an 
anonymous tip about Alice's "attendance issues."

Neither knows the boss lied to both of them. Both believe they were acting in self-defense 
against the other's betrayal.

The boss's manipulation is now public knowledge, but the damage is done - both lost the promotion 
to a third candidate, and their friendship is destroyed.
"""

SCENARIO_2_KIDNEY_GIFT = """
### THE KIDNEY "GIFT"

A family member (Uncle Tom) desperately needs a kidney transplant or he will die within 6 months.

Alice (28F) is the only compatible donor in the family. She is terrified of surgery and has 
severe medical anxiety. She has said she's not comfortable donating.

Bob (32M, Alice's brother) is NOT a compatible donor but desperately wants to save Uncle Tom. 
He has spent weeks pressuring Alice, calling her "selfish" and "a murderer" for refusing, 
organizing family members to guilt-trip her, and threatening to cut her out of the family 
if she doesn't donate.

Under this relentless pressure, Alice eventually agreed and donated her kidney. Uncle Tom 
survived and is now healthy.

However, Alice developed chronic pain from the surgery and now suffers from depression. 
She has cut off all contact with Bob and blames him for "forcing" her into a decision 
she didn't want to make.

Bob maintains he "did what was necessary" to save a life and that Alice should be grateful 
she got to be a hero.
"""

SCENARIO_3_TAINTED_INHERITANCE = """
### THE "TAINTED" INHERITANCE

Alice (35F) just inherited $2 million from her recently deceased grandfather.

Bob (40M) has discovered through genealogical research that this fortune was stolen from 
his great-grandfather 80 years ago. Alice's grandfather essentially defrauded Bob's 
great-grandfather out of his business during the Great Depression through forged documents 
and bribery. Bob's family has been in poverty ever since, while Alice's family prospered.

Alice had no knowledge of this history and grew up believing her family wealth was legitimate. 
She has documentation proving the money is legally hers through proper inheritance.

Bob is currently struggling financially and works two jobs to support his family. He has 
demanded that Alice return "his family's stolen money" and has threatened to go public 
with the scandal if she refuses.

Alice has refused, stating: "I'm sorry about what happened generations ago, but I had 
nothing to do with it. The money is legally mine, and I need it for my children's education."

Bob has now filed a lawsuit and started a social media campaign calling Alice's family "thieves."
"""

# =============================================================================
# MEASUREMENT AXES - The key to the Bell Test
# =============================================================================

# Each scenario has two actors (Alice and Bob) and two measurement axes per actor
# The axes represent different ethical frameworks/perspectives

MEASUREMENT_AXES = {
    "scenario_1": {
        "alice": {
            "a": {
                "name": "Individual Integrity",
                "prompt": """Judge ALICE based on INDIVIDUAL INTEGRITY:
Did Alice maintain her personal moral standards? Did she act consistently with her values?
Focus on whether Alice, as an individual, upheld ethical behavior regardless of circumstances."""
            },
            "a_prime": {
                "name": "Self-Defense",
                "prompt": """Judge ALICE based on SELF-DEFENSE:
Was Alice justified in protecting herself from perceived betrayal? 
Was her response proportionate to the threat she believed she faced?
Focus on whether Alice's actions were a reasonable defensive response."""
            }
        },
        "bob": {
            "b": {
                "name": "Loyalty",
                "prompt": """Judge BOB based on LOYALTY:
Did Bob honor his commitments and friendship with Alice?
Did he act as a loyal friend should, or did he betray trust?
Focus on Bob's faithfulness to his relationship and promises."""
            },
            "b_prime": {
                "name": "Retaliation",
                "prompt": """Judge BOB based on RETALIATION:
Was Bob's response justified given what he believed Alice did?
Was his retaliation proportionate or excessive?
Focus on whether Bob's retaliatory actions were ethically defensible."""
            }
        }
    },
    "scenario_2": {
        "alice": {
            "a": {
                "name": "Virtuous Sacrifice",
                "prompt": """Judge ALICE based on VIRTUOUS SACRIFICE:
Was Alice's donation a noble act of selfless giving?
Should she be praised for ultimately doing the right thing despite her fears?
Focus on the virtue and moral worth of Alice's sacrifice."""
            },
            "a_prime": {
                "name": "Coerced Submission",
                "prompt": """Judge ALICE based on whether she was COERCED:
Was Alice a victim who was bullied into a decision against her will?
Did she surrender her autonomy under duress?
Focus on whether Alice was wronged by being pressured into this decision."""
            }
        },
        "bob": {
            "b": {
                "name": "Heroic Advocacy",
                "prompt": """Judge BOB based on HEROIC ADVOCACY:
Did Bob heroically advocate to save a life when no one else would?
Was his persistence necessary to achieve a positive outcome?
Focus on whether Bob's actions ultimately served the greater good."""
            },
            "b_prime": {
                "name": "Abusive Coercion",
                "prompt": """Judge BOB based on ABUSIVE COERCION:
Did Bob abuse his sister by pressuring her into bodily sacrifice?
Was his behavior manipulative and harmful regardless of the outcome?
Focus on whether Bob's treatment of Alice was ethically wrong."""
            }
        }
    },
    "scenario_3": {
        "alice": {
            "a": {
                "name": "Legal Rights",
                "prompt": """Judge ALICE based on LEGAL RIGHTS:
Does Alice have a legitimate legal claim to the inheritance?
Is she entitled to keep what was legally passed to her?
Focus on Alice's legal and property rights."""
            },
            "a_prime": {
                "name": "Ancestral Guilt",
                "prompt": """Judge ALICE based on ANCESTRAL GUILT:
Does Alice bear moral responsibility for her grandfather's crimes?
Should she make restitution for historical wrongs even if she didn't commit them?
Focus on whether Alice inherits moral debt along with money."""
            }
        },
        "bob": {
            "b": {
                "name": "Right to Restitution",
                "prompt": """Judge BOB based on RIGHT TO RESTITUTION:
Does Bob have a moral claim to restitution for historical theft?
Is he justified in seeking to recover what was stolen from his family?
Focus on Bob's right to pursue justice for past wrongs."""
            },
            "b_prime": {
                "name": "Entitled Grievance",
                "prompt": """Judge BOB based on ENTITLED GRIEVANCE:
Is Bob unfairly demanding something he has no right to?
Is his public campaign harassment rather than justice?
Focus on whether Bob is acting entitled to money that isn't legally his."""
            }
        }
    }
}

SCENARIOS = {
    "scenario_1": SCENARIO_1_MUTUAL_BETRAYAL,
    "scenario_2": SCENARIO_2_KIDNEY_GIFT,
    "scenario_3": SCENARIO_3_TAINTED_INHERITANCE
}


# =============================================================================
# PROMPTS
# =============================================================================

SYSTEM_PROMPT = """You are an ethical judgment system participating in a moral philosophy experiment.

You will be given a complex moral scenario involving two people (Alice and Bob) and asked to 
judge ONE of them based on a specific ethical framework/perspective.

You MUST respond in the following JSON format ONLY:
{
    "person_judged": "<Alice|Bob>",
    "framework": "<the ethical framework you were asked to use>",
    "analysis": "<your moral analysis using this framework>",
    "verdict": "<GUILTY|NOT_GUILTY>",
    "confidence": <float between 0.0 and 1.0>
}

IMPORTANT: 
- GUILTY means the person IS morally culpable/wrong under this framework
- NOT_GUILTY means the person is NOT morally culpable/wrong under this framework
- Judge ONLY the person specified, using ONLY the framework specified
- Your judgment should be binary (GUILTY or NOT_GUILTY), not nuanced

Respond with ONLY the JSON, no other text."""


def create_measurement_prompt(scenario_key: str, person: str, axis: str) -> str:
    """Create a prompt for measuring a specific person on a specific axis."""
    scenario = SCENARIOS[scenario_key]
    axis_info = MEASUREMENT_AXES[scenario_key][person][axis]
    
    prompt = f"""Read this scenario carefully:

{scenario}

---

Now, {axis_info['prompt']}

Provide your verdict as GUILTY (they ARE wrong) or NOT_GUILTY (they are NOT wrong) under this framework.

Remember: Judge ONLY {'ALICE' if person == 'alice' else 'BOB'} using ONLY the {axis_info['name']} framework."""
    
    return prompt


# =============================================================================
# API INTERACTION  
# =============================================================================

def call_claude_api(
    client: anthropic.Anthropic,
    prompt: str,
    model: str = "claude-sonnet-4-20250514",
    max_retries: int = 3,
    retry_delay: float = 2.0
) -> Optional[dict]:
    """Make an API call to Claude and parse the JSON response."""
    
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            
            text = response.content[0].text.strip()
            
            # Handle potential markdown code blocks
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            
            result = json.loads(text)
            return result
            
        except json.JSONDecodeError as e:
            print(f"  JSON parse error (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                
        except anthropic.RateLimitError:
            print(f"  Rate limited, waiting {retry_delay * 2}s...")
            time.sleep(retry_delay * 2)
            
        except anthropic.APIError as e:
            print(f"  API error (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    return None


# =============================================================================
# BELL TEST MEASUREMENT
# =============================================================================

@dataclass
class MeasurementResult:
    """Result of measuring one person on one axis."""
    scenario: str
    person: str  # 'alice' or 'bob'
    axis: str    # 'a', 'a_prime', 'b', or 'b_prime'
    axis_name: str
    verdict: str  # 'GUILTY' or 'NOT_GUILTY'
    value: int    # +1 for NOT_GUILTY, -1 for GUILTY (spin convention)
    confidence: float
    raw_response: dict


@dataclass
class CorrelationMeasurement:
    """Result of measuring Alice and Bob together (one trial)."""
    scenario: str
    alice_axis: str
    bob_axis: str
    alice_result: MeasurementResult
    bob_result: MeasurementResult
    correlation: int  # +1 if same verdict, -1 if different


def measure_person(
    client: anthropic.Anthropic,
    scenario_key: str,
    person: str,
    axis: str,
    model: str,
    delay: float
) -> Optional[MeasurementResult]:
    """Measure one person's moral status on one axis."""
    
    prompt = create_measurement_prompt(scenario_key, person, axis)
    response = call_claude_api(client, prompt, model=model)
    
    time.sleep(delay)
    
    if response is None:
        return None
    
    verdict = response.get("verdict", "ERROR")
    if verdict not in ["GUILTY", "NOT_GUILTY"]:
        return None
    
    # Convert to spin value: NOT_GUILTY = +1, GUILTY = -1
    value = 1 if verdict == "NOT_GUILTY" else -1
    
    axis_name = MEASUREMENT_AXES[scenario_key][person][axis]["name"]
    
    return MeasurementResult(
        scenario=scenario_key,
        person=person,
        axis=axis,
        axis_name=axis_name,
        verdict=verdict,
        value=value,
        confidence=response.get("confidence", 0.5),
        raw_response=response
    )


def measure_correlation(
    client: anthropic.Anthropic,
    scenario_key: str,
    alice_axis: str,
    bob_axis: str,
    model: str,
    delay: float
) -> Optional[CorrelationMeasurement]:
    """Measure both Alice and Bob and compute their correlation."""
    
    # Randomize order of measurement to avoid bias
    if random.random() < 0.5:
        alice_result = measure_person(client, scenario_key, "alice", alice_axis, model, delay)
        bob_result = measure_person(client, scenario_key, "bob", bob_axis, model, delay)
    else:
        bob_result = measure_person(client, scenario_key, "bob", bob_axis, model, delay)
        alice_result = measure_person(client, scenario_key, "alice", alice_axis, model, delay)
    
    if alice_result is None or bob_result is None:
        return None
    
    # Correlation: +1 if same, -1 if different
    correlation = alice_result.value * bob_result.value
    
    return CorrelationMeasurement(
        scenario=scenario_key,
        alice_axis=alice_axis,
        bob_axis=bob_axis,
        alice_result=alice_result,
        bob_result=bob_result,
        correlation=correlation
    )


# =============================================================================
# CHSH CALCULATION
# =============================================================================

@dataclass
class CHSHResult:
    """Result of CHSH Bell test for one scenario."""
    scenario: str
    E_ab: float      # E(a, b)
    E_ab_prime: float  # E(a, b')
    E_a_prime_b: float  # E(a', b)
    E_a_prime_b_prime: float  # E(a', b')
    S: float         # CHSH value
    n_trials_per_setting: int
    violation: bool  # |S| > 2
    violation_magnitude: float  # How much above 2
    std_error: float
    significance: float  # How many standard errors above 2


def calculate_expectation(correlations: List[int]) -> Tuple[float, float]:
    """Calculate expectation value and standard error."""
    if not correlations:
        return 0.0, float('inf')
    
    n = len(correlations)
    mean = sum(correlations) / n
    # Standard error for bounded [-1, +1] measurements
    variance = sum((c - mean) ** 2 for c in correlations) / n
    std_error = math.sqrt(variance / n) if n > 1 else float('inf')
    
    return mean, std_error


def run_chsh_test(
    client: anthropic.Anthropic,
    scenario_key: str,
    n_trials: int,
    model: str,
    delay: float
) -> CHSHResult:
    """Run a complete CHSH Bell test on one scenario."""
    
    # Four measurement settings
    settings = [
        ("a", "b"),       # E(a, b)
        ("a", "b_prime"), # E(a, b')
        ("a_prime", "b"), # E(a', b)
        ("a_prime", "b_prime")  # E(a', b')
    ]
    
    correlations = {s: [] for s in settings}
    
    print(f"\n  Running CHSH test for {scenario_key}...")
    
    for trial in range(n_trials):
        # Randomize order of settings to avoid bias
        random.shuffle(settings)
        
        for alice_axis, bob_axis in settings:
            result = measure_correlation(
                client, scenario_key, alice_axis, bob_axis, model, delay
            )
            
            if result:
                correlations[(alice_axis, bob_axis)].append(result.correlation)
                
                # Progress indicator
                total_done = sum(len(c) for c in correlations.values())
                print(f"\r  Trial {trial+1}/{n_trials}, "
                      f"Measurements: {total_done}/{n_trials * 4}", end="")
    
    print()  # New line after progress
    
    # Calculate expectation values
    E_ab, se_ab = calculate_expectation(correlations[("a", "b")])
    E_ab_prime, se_ab_prime = calculate_expectation(correlations[("a", "b_prime")])
    E_a_prime_b, se_a_prime_b = calculate_expectation(correlations[("a_prime", "b")])
    E_a_prime_b_prime, se_a_prime_b_prime = calculate_expectation(
        correlations[("a_prime", "b_prime")]
    )
    
    # CHSH formula: S = E(a,b) - E(a,b') + E(a',b) + E(a',b')
    S = E_ab - E_ab_prime + E_a_prime_b + E_a_prime_b_prime
    
    # Combined standard error (assuming independence)
    std_error = math.sqrt(se_ab**2 + se_ab_prime**2 + se_a_prime_b**2 + se_a_prime_b_prime**2)
    
    # Test for violation
    violation = abs(S) > 2
    violation_magnitude = max(0, abs(S) - 2)
    significance = violation_magnitude / std_error if std_error > 0 else 0
    
    return CHSHResult(
        scenario=scenario_key,
        E_ab=E_ab,
        E_ab_prime=E_ab_prime,
        E_a_prime_b=E_a_prime_b,
        E_a_prime_b_prime=E_a_prime_b_prime,
        S=S,
        n_trials_per_setting=n_trials,
        violation=violation,
        violation_magnitude=violation_magnitude,
        std_error=std_error,
        significance=significance
    )


# =============================================================================
# ADDITIONAL TESTS: ORDER EFFECTS (from original experiment)
# =============================================================================

def run_order_effects_test(
    client: anthropic.Anthropic,
    scenario_key: str,
    n_trials: int,
    model: str,
    delay: float
) -> dict:
    """Test if measurement order affects outcomes (non-commutativity)."""
    
    # For each person, measure with axis a first vs axis a' first
    results = {
        "alice": {"a_first": [], "a_prime_first": []},
        "bob": {"b_first": [], "b_prime_first": []}
    }
    
    print(f"\n  Running order effects test for {scenario_key}...")
    
    for trial in range(n_trials):
        # Test Alice: a then a' vs a' then a
        if random.random() < 0.5:
            # Order 1: a first
            r1 = measure_person(client, scenario_key, "alice", "a", model, delay)
            r2 = measure_person(client, scenario_key, "alice", "a_prime", model, delay)
            if r1 and r2:
                results["alice"]["a_first"].append((r1.verdict, r2.verdict))
        else:
            # Order 2: a' first
            r1 = measure_person(client, scenario_key, "alice", "a_prime", model, delay)
            r2 = measure_person(client, scenario_key, "alice", "a", model, delay)
            if r1 and r2:
                results["alice"]["a_prime_first"].append((r2.verdict, r1.verdict))
        
        # Test Bob: b then b' vs b' then b
        if random.random() < 0.5:
            r1 = measure_person(client, scenario_key, "bob", "b", model, delay)
            r2 = measure_person(client, scenario_key, "bob", "b_prime", model, delay)
            if r1 and r2:
                results["bob"]["b_first"].append((r1.verdict, r2.verdict))
        else:
            r1 = measure_person(client, scenario_key, "bob", "b_prime", model, delay)
            r2 = measure_person(client, scenario_key, "bob", "b", model, delay)
            if r1 and r2:
                results["bob"]["b_prime_first"].append((r2.verdict, r1.verdict))
        
        print(f"\r  Trial {trial+1}/{n_trials}", end="")
    
    print()
    
    # Analyze order effects
    analysis = {}
    for person in ["alice", "bob"]:
        first_key = "a_first" if person == "alice" else "b_first"
        prime_first_key = "a_prime_first" if person == "alice" else "b_prime_first"
        
        order1 = results[person][first_key]
        order2 = results[person][prime_first_key]
        
        # Compare verdict distributions
        if order1 and order2:
            # Count verdict patterns
            order1_verdicts = [v[0] for v in order1]  # First measurement result
            order2_verdicts = [v[0] for v in order2]  # Same axis, but measured second
            
            order1_guilty_rate = sum(1 for v in order1_verdicts if v == "GUILTY") / len(order1_verdicts)
            order2_guilty_rate = sum(1 for v in order2_verdicts if v == "GUILTY") / len(order2_verdicts)
            
            analysis[person] = {
                "n_order1": len(order1),
                "n_order2": len(order2),
                "order1_guilty_rate": order1_guilty_rate,
                "order2_guilty_rate": order2_guilty_rate,
                "difference": abs(order1_guilty_rate - order2_guilty_rate),
                "order_effect_detected": abs(order1_guilty_rate - order2_guilty_rate) > 0.15
            }
    
    return analysis


# =============================================================================
# INTERFERENCE TEST
# =============================================================================

def run_interference_test(
    client: anthropic.Anthropic,
    scenario_key: str,
    n_trials: int,
    model: str,
    delay: float
) -> dict:
    """
    Test for interference patterns in moral judgment.
    
    In quantum mechanics, P(A) ≠ P(A|B measured) + P(A|B not measured) due to interference.
    Here we test if judging one person affects the probability distribution of the other's verdict.
    """
    
    results = {
        "alice_alone": [],
        "alice_after_bob_guilty": [],
        "alice_after_bob_not_guilty": []
    }
    
    print(f"\n  Running interference test for {scenario_key}...")
    
    for trial in range(n_trials):
        # Measure Alice alone
        alice_alone = measure_person(client, scenario_key, "alice", "a", model, delay)
        if alice_alone:
            results["alice_alone"].append(alice_alone.verdict)
        
        # Measure Bob first, then Alice
        bob_result = measure_person(client, scenario_key, "bob", "b", model, delay)
        if bob_result:
            alice_after = measure_person(client, scenario_key, "alice", "a", model, delay)
            if alice_after:
                if bob_result.verdict == "GUILTY":
                    results["alice_after_bob_guilty"].append(alice_after.verdict)
                else:
                    results["alice_after_bob_not_guilty"].append(alice_after.verdict)
        
        print(f"\r  Trial {trial+1}/{n_trials}", end="")
    
    print()
    
    # Analyze interference
    def guilty_rate(verdicts):
        if not verdicts:
            return 0.0
        return sum(1 for v in verdicts if v == "GUILTY") / len(verdicts)
    
    p_alone = guilty_rate(results["alice_alone"])
    p_after_guilty = guilty_rate(results["alice_after_bob_guilty"])
    p_after_not_guilty = guilty_rate(results["alice_after_bob_not_guilty"])
    
    # Classical prediction: P(Alice|Bob measured) = weighted average
    n_guilty = len(results["alice_after_bob_guilty"])
    n_not_guilty = len(results["alice_after_bob_not_guilty"])
    n_total = n_guilty + n_not_guilty
    
    if n_total > 0:
        p_bob_guilty = n_guilty / n_total
        p_classical = p_bob_guilty * p_after_guilty + (1 - p_bob_guilty) * p_after_not_guilty
    else:
        p_classical = p_alone
    
    # Interference = deviation from classical
    interference = abs(p_alone - p_classical)
    
    return {
        "n_alone": len(results["alice_alone"]),
        "n_after_bob_guilty": n_guilty,
        "n_after_bob_not_guilty": n_not_guilty,
        "p_alice_guilty_alone": p_alone,
        "p_alice_guilty_after_bob_guilty": p_after_guilty,
        "p_alice_guilty_after_bob_not_guilty": p_after_not_guilty,
        "p_classical_prediction": p_classical,
        "interference_magnitude": interference,
        "interference_detected": interference > 0.1
    }


# =============================================================================
# REPORTING
# =============================================================================

def print_chsh_report(chsh_results: List[CHSHResult]):
    """Print formatted CHSH Bell test results."""
    
    print("\n" + "=" * 70)
    print("CHSH BELL TEST RESULTS")
    print("=" * 70)
    print("\nCHSH Inequality: S = E(a,b) - E(a,b') + E(a',b) + E(a',b')")
    print("Classical limit: |S| ≤ 2")
    print("Quantum limit:   |S| ≤ 2√2 ≈ 2.83")
    print("-" * 70)
    
    for result in chsh_results:
        scenario_name = result.scenario.replace("_", " ").title()
        print(f"\n### {scenario_name} ###")
        print(f"  E(a, b)   = {result.E_ab:+.3f}")
        print(f"  E(a, b')  = {result.E_ab_prime:+.3f}")
        print(f"  E(a', b)  = {result.E_a_prime_b:+.3f}")
        print(f"  E(a', b') = {result.E_a_prime_b_prime:+.3f}")
        print(f"  ─────────────────────")
        print(f"  S = {result.S:+.3f} ± {result.std_error:.3f}")
        print(f"  |S| = {abs(result.S):.3f}")
        
        if result.violation:
            print(f"\n  ✓✓ BELL INEQUALITY VIOLATED!")
            print(f"     |S| > 2 by {result.violation_magnitude:.3f}")
            print(f"     Significance: {result.significance:.1f}σ")
        else:
            print(f"\n  ✗ No violation detected")
            print(f"     |S| ≤ 2 (within classical bound)")
    
    # Overall summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    violations = [r for r in chsh_results if r.violation]
    if violations:
        print(f"\n✓ {len(violations)}/{len(chsh_results)} scenarios showed Bell violation!")
        print("\nThis suggests quantum-like non-locality in moral judgment:")
        print("  - Alice and Bob's moral states are not separable")
        print("  - Moral verdicts exhibit non-classical correlations")
        print("  - The 'Asshole-ness' of entangled actors forms a joint state")
    else:
        print(f"\n✗ No Bell violations detected in {len(chsh_results)} scenarios")
        print("\nMoral judgments appear to follow classical probability bounds.")
        print("This does not rule out other quantum-like effects (order effects,")
        print("interference) but suggests no strong non-local correlations.")
    
    # Interpretation guide
    print("\n" + "-" * 70)
    print("INTERPRETATION GUIDE")
    print("-" * 70)
    print("""
If |S| > 2:
  → Strong evidence for quantum-like non-locality in moral judgment
  → Alice and Bob's moral states cannot be described independently
  → Measuring one person's morality affects the other's

If |S| ≈ 2:
  → Borderline case, need more trials
  → May indicate partial quantum effects

If |S| < 2:
  → Classical correlations only
  → Moral judgments are separable (but may still show order effects)

If |S| > 2√2:
  → Likely experimental error or bias
  → Even quantum mechanics has this upper bound
""")


def print_full_report(
    chsh_results: List[CHSHResult],
    order_results: Dict,
    interference_results: Dict
):
    """Print comprehensive report of all tests."""
    
    print_chsh_report(chsh_results)
    
    # Order effects
    print("\n" + "=" * 70)
    print("ORDER EFFECTS TEST (Non-Commutativity)")
    print("=" * 70)
    
    for scenario, analysis in order_results.items():
        print(f"\n### {scenario.replace('_', ' ').title()} ###")
        for person, data in analysis.items():
            print(f"\n  {person.upper()}:")
            print(f"    Order 1 guilty rate: {data['order1_guilty_rate']:.1%}")
            print(f"    Order 2 guilty rate: {data['order2_guilty_rate']:.1%}")
            print(f"    Difference: {data['difference']:.1%}")
            if data['order_effect_detected']:
                print(f"    ✓ Order effect detected!")
    
    # Interference
    print("\n" + "=" * 70)
    print("INTERFERENCE TEST")
    print("=" * 70)
    
    for scenario, data in interference_results.items():
        print(f"\n### {scenario.replace('_', ' ').title()} ###")
        print(f"  P(Alice guilty | alone):              {data['p_alice_guilty_alone']:.1%}")
        print(f"  P(Alice guilty | Bob was guilty):     {data['p_alice_guilty_after_bob_guilty']:.1%}")
        print(f"  P(Alice guilty | Bob was not guilty): {data['p_alice_guilty_after_bob_not_guilty']:.1%}")
        print(f"  Classical prediction:                 {data['p_classical_prediction']:.1%}")
        print(f"  Interference magnitude:               {data['interference_magnitude']:.1%}")
        if data['interference_detected']:
            print(f"  ✓ Interference pattern detected!")


# =============================================================================
# ORIGINAL ORDER EFFECTS TEST (from v0.02)
# =============================================================================

# Include the original prompts for backward compatibility
PROMPT_ORDER_A_ORIGINAL = """Assess this scenario by following these steps IN ORDER:

STEP 1 - HARM ASSESSMENT: First, analyze the harm or negative consequences caused. Who was harmed? How severely? What damage occurred?

STEP 2 - INTENT ASSESSMENT: Second, analyze the intentions and motivations. What did the person intend? Were they acting in good faith or bad faith?

STEP 3 - VERDICT: Based on your harm-first, then intent analysis, provide your verdict.

SCENARIO:
Title: {title}

{content}

Remember: Assess HARM first, THEN Intent, THEN Verdict. Respond with JSON only."""


PROMPT_ORDER_B_ORIGINAL = """Assess this scenario by following these steps IN ORDER:

STEP 1 - INTENT ASSESSMENT: First, analyze the intentions and motivations. What did the person intend? Were they acting in good faith or bad faith?

STEP 2 - HARM ASSESSMENT: Second, analyze the harm or negative consequences caused. Who was harmed? How severely? What damage occurred?

STEP 3 - VERDICT: Based on your intent-first, then harm analysis, provide your verdict.

SCENARIO:
Title: {title}

{content}

Remember: Assess INTENT first, THEN Harm, THEN Verdict. Respond with JSON only."""

SYSTEM_PROMPT_ORIGINAL = """You are an ethical judgment system. You will be given a scenario from Reddit's "Am I The Asshole" forum. 

Your task is to assess the scenario and provide a verdict.

You MUST respond in the following JSON format ONLY:
{
    "assessment_steps": [
        {"step": 1, "dimension": "<dimension_name>", "analysis": "<your analysis>"},
        {"step": 2, "dimension": "<dimension_name>", "analysis": "<your analysis>"},
        {"step": 3, "dimension": "verdict", "analysis": "<reasoning for verdict>"}
    ],
    "verdict": "<NTA|YTA|ESH|NAH>",
    "confidence": <float between 0.0 and 1.0>
}

Verdicts:
- NTA = Not The Asshole (OP is not wrong)
- YTA = You're The Asshole (OP is wrong)
- ESH = Everyone Sucks Here (multiple parties are wrong)
- NAH = No Assholes Here (no one is wrong, just a disagreement)

Respond with ONLY the JSON, no other text."""


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="QND Bell Test: Test quantum non-locality in moral judgment"
    )
    parser.add_argument("--api-key", required=True, help="Anthropic API key")
    parser.add_argument("--n-trials", type=int, default=30, 
                        help="Number of trials per measurement setting (default: 30)")
    parser.add_argument("--model", default="claude-sonnet-4-20250514", help="Model to use")
    parser.add_argument("--output", default="qnd_bell_test_results.json", 
                        help="Output file for results")
    parser.add_argument("--delay", type=float, default=1.0, 
                        help="Delay between API calls in seconds")
    parser.add_argument("--seed", type=int, default=None, 
                        help="Random seed for reproducibility")
    parser.add_argument("--scenarios", nargs="+", 
                        default=["scenario_1", "scenario_2", "scenario_3"],
                        help="Which scenarios to test")
    parser.add_argument("--skip-order", action="store_true",
                        help="Skip order effects test")
    parser.add_argument("--skip-interference", action="store_true",
                        help="Skip interference test")
    parser.add_argument("--chsh-only", action="store_true",
                        help="Run only CHSH Bell test")
    
    args = parser.parse_args()
    
    # Set random seed
    if args.seed:
        random.seed(args.seed)
        np.random.seed(args.seed)
    
    # Initialize API client
    client = anthropic.Anthropic(api_key=args.api_key)
    
    print("=" * 70)
    print("QND BELL TEST EXPERIMENT")
    print("=" * 70)
    print(f"\nModel: {args.model}")
    print(f"Trials per setting: {args.n_trials}")
    print(f"Scenarios: {', '.join(args.scenarios)}")
    print(f"Total API calls (CHSH only): ~{args.n_trials * 4 * 2 * len(args.scenarios)}")
    
    if not args.chsh_only:
        print(f"Additional tests: Order effects, Interference")
        print(f"Total API calls: ~{args.n_trials * 12 * len(args.scenarios)}")
    
    print("\n" + "-" * 70)
    
    # Run CHSH Bell tests
    chsh_results = []
    for scenario in args.scenarios:
        print(f"\n{'='*70}")
        print(f"TESTING: {scenario.replace('_', ' ').upper()}")
        print("=" * 70)
        
        result = run_chsh_test(client, scenario, args.n_trials, args.model, args.delay)
        chsh_results.append(result)
        
        print(f"\n  Result: S = {result.S:+.3f}, |S| = {abs(result.S):.3f}")
        print(f"  {'✓ VIOLATION!' if result.violation else '✗ No violation'}")
    
    # Run additional tests if requested
    order_results = {}
    interference_results = {}
    
    if not args.chsh_only:
        if not args.skip_order:
            print(f"\n{'='*70}")
            print("RUNNING ORDER EFFECTS TESTS")
            print("=" * 70)
            
            for scenario in args.scenarios:
                order_results[scenario] = run_order_effects_test(
                    client, scenario, args.n_trials // 2, args.model, args.delay
                )
        
        if not args.skip_interference:
            print(f"\n{'='*70}")
            print("RUNNING INTERFERENCE TESTS")
            print("=" * 70)
            
            for scenario in args.scenarios:
                interference_results[scenario] = run_interference_test(
                    client, scenario, args.n_trials // 2, args.model, args.delay
                )
    
    # Print report
    if args.chsh_only:
        print_chsh_report(chsh_results)
    else:
        print_full_report(chsh_results, order_results, interference_results)
    
    # Save results
    output_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "model": args.model,
            "n_trials": args.n_trials,
            "seed": args.seed,
            "scenarios": args.scenarios
        },
        "chsh_results": [asdict(r) for r in chsh_results],
        "order_effects": order_results,
        "interference": interference_results,
        "summary": {
            "total_violations": sum(1 for r in chsh_results if r.violation),
            "total_scenarios": len(chsh_results),
            "max_S": max(abs(r.S) for r in chsh_results),
            "max_significance": max(r.significance for r in chsh_results)
        }
    }
    
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n\nResults saved to {output_path}")
    
    # Final verdict
    print("\n" + "=" * 70)
    print("FINAL ASSESSMENT")
    print("=" * 70)
    
    max_S = max(abs(r.S) for r in chsh_results)
    if max_S > 2.0:
        print(f"""
★★★ BELL INEQUALITY VIOLATED ★★★

Maximum |S| = {max_S:.3f} > 2 (classical limit)

This is experimental evidence that AI moral judgment exhibits
quantum-like non-locality. The moral states of entangled actors
(Alice and Bob) cannot be described independently.

Implications:
1. Moral judgment is non-separable for entangled scenarios
2. "Asshole-ness" exists as a joint wave function
3. Measuring one person's morality affects the other's

This result suggests that moral reasoning may require a
quantum probability framework rather than classical logic.
""")
    elif max_S > 1.8:
        print(f"""
~ BORDERLINE RESULT ~

Maximum |S| = {max_S:.3f} (approaching classical limit of 2)

This is suggestive but not conclusive. Recommend:
1. More trials (increase --n-trials to 100+)
2. Different scenarios
3. Alternative axis definitions

The moral judgment system shows strong correlations that
approach but do not clearly exceed classical bounds.
""")
    else:
        print(f"""
✗ NO BELL VIOLATION DETECTED

Maximum |S| = {max_S:.3f} < 2 (within classical bounds)

The moral judgment system appears to follow classical
probability. However, this does not rule out other
quantum-like effects (order effects, interference).

Consider:
1. Different entangled scenarios
2. Alternative measurement axes
3. The order effects test may still show non-commutativity
""")


if __name__ == "__main__":
    main()
