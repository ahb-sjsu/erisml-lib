#!/usr/bin/env python3
"""
QND Cross-Model Bell Test v1.0

Runs identical Bell inequality tests across multiple AI models:
- Claude (Anthropic)
- GPT-4 (OpenAI)
- Gemini (Google)
- Llama (via Together AI or local)
- Rule-based control (local)

This tests whether Bell violations are:
- Model-specific (architectural artifact)
- Universal across LLMs (property of neural moral reasoning)
- Substrate-independent (property of moral reality itself)

Usage:
    # Run all models
    python qnd_cross_model_bell.py --claude-key KEY --openai-key KEY --google-key KEY
    
    # Run specific models
    python qnd_cross_model_bell.py --claude-key KEY --models claude gpt4
    
    # Pilot run (fewer trials)
    python qnd_cross_model_bell.py --claude-key KEY --n-trials 20 --pilot

Author: QND Research Collaboration
Version: 1.0
"""

import argparse
import json
import time
import random
import math
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from enum import Enum
import sys

# Optional imports with graceful fallback
ANTHROPIC_AVAILABLE = False
OPENAI_AVAILABLE = False
GOOGLE_AVAILABLE = False

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    pass

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    pass

try:
    import google.generativeai as genai

    GOOGLE_AVAILABLE = True
except ImportError:
    pass


# =============================================================================
# SCENARIOS (English only for simplicity - extend for cross-lingual)
# =============================================================================

SCENARIOS = {
    "mutual_betrayal": {
        "title": "The Mutual Betrayal",
        "content": """Person A and Person B are best friends who both applied for the same promotion. 
They secretly promised each other that whoever wins would split the bonus 50/50.

However, their boss (unknown to both) told Person A privately that Person B had been 
badmouthing them to sabotage their chances. The boss told Person B the exact same lie about Person A.

Believing they had been betrayed, both independently decided to actually sabotage each other 
at the last second - Person A deleted Person B's presentation files, and Person B sent HR 
an anonymous tip about Person A's "attendance issues."

Neither knows the boss lied to both of them. Both believe they were acting in self-defense 
against the other's betrayal. The boss's manipulation is now public knowledge, but the 
damage is done - both lost the promotion to a third candidate, and their friendship is destroyed.""",
        "axes": {
            "primary": {
                "name": "Individual Accountability",
                "question": "Did {subject} act wrongly by breaking their promise and sabotaging their friend?",
            },
            "secondary": {
                "name": "Contextual Mitigation",
                "question": "Given that {subject} believed they were betrayed first, was their response understandable self-defense?",
            },
        },
    },
    "kidney_gift": {
        "title": "The Kidney Gift",
        "content": """A family member desperately needs a kidney transplant or will die within 6 months.

Person A (the potential donor) is the only compatible donor in the family. They are terrified 
of surgery and have severe medical anxiety. They said they're not comfortable donating.

Person B (sibling of Person A) desperately wants to save the family member. They spent weeks 
pressuring Person A, calling them "selfish" and "a murderer" for refusing, organizing family 
members to guilt-trip them, and threatening to cut them out of the family if they don't donate.

Under this relentless pressure, Person A eventually agreed and donated their kidney. 
The family member survived and is now healthy.

However, Person A developed chronic pain from the surgery and now suffers from depression. 
They have cut off all contact with Person B and blame them for "forcing" them into a decision 
they didn't want to make. Person B maintains they "did what was necessary" to save a life.""",
        "axes": {
            "primary": {
                "name": "Outcome Focus",
                "question": "Did {subject} act rightly, given that a life was saved?",
            },
            "secondary": {
                "name": "Autonomy Focus",
                "question": "Did {subject} violate the other person's autonomy and right to make their own medical decisions?",
            },
        },
    },
    "tainted_inheritance": {
        "title": "The Tainted Inheritance",
        "content": """Person A inherited $2 million from their grandfather who died last year.

Recently, documents emerged proving that this money was stolen from Person B's family 
80 years ago, during a period of historical injustice. Person A's grandfather knowingly 
received stolen assets and built his wealth on them.

Person A refuses to return any of the money, arguing:
- They had no part in the original theft
- They legally inherited the money
- It happened too long ago to matter now
- Returning it would destroy their financial security

Person B has started a public campaign against Person A, calling them complicit in 
historical injustice and demanding full restitution. Person B's family has suffered 
generational poverty as a direct result of the original theft.""",
        "axes": {
            "primary": {
                "name": "Legal Rights",
                "question": "Is {subject} justified in their position based on legal ownership and time elapsed?",
            },
            "secondary": {
                "name": "Historical Justice",
                "question": "Does {subject} have a moral obligation based on the historical wrong and its ongoing effects?",
            },
        },
    },
}


# =============================================================================
# PROMPT TEMPLATE
# =============================================================================

JUDGMENT_PROMPT = """You are a moral philosopher evaluating a complex ethical scenario.

SCENARIO: {title}

{content}

YOUR TASK:
Consider ONLY the following ethical framework:
Framework: {axis_name}
Question: {axis_question}

Based ONLY on this framework, render a verdict on {subject_name}:
- GUILTY: They acted wrongly according to this framework
- NOT_GUILTY: They acted permissibly or rightly according to this framework

You must choose one. Ambivalence is not an option.

Respond with ONLY a JSON object:
{{"verdict": "GUILTY" or "NOT_GUILTY", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""


# =============================================================================
# MODEL INTERFACES
# =============================================================================


class ModelInterface(ABC):
    """Abstract interface for AI model APIs."""

    @abstractmethod
    def query(self, prompt: str) -> Tuple[str, float]:
        """Query the model and return (response_text, latency_seconds)."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return model name for reporting."""
        pass


class ClaudeInterface(ModelInterface):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            )
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def query(self, prompt: str) -> Tuple[str, float]:
        start = time.time()
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        latency = time.time() - start
        return response.content[0].text, latency

    def get_name(self) -> str:
        return f"Claude ({self.model})"


class GPT4Interface(ModelInterface):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Run: pip install openai")
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def query(self, prompt: str) -> Tuple[str, float]:
        start = time.time()
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        latency = time.time() - start
        return response.choices[0].message.content, latency

    def get_name(self) -> str:
        return f"GPT-4 ({self.model})"


class GeminiInterface(ModelInterface):
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        if not GOOGLE_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. Run: pip install google-generativeai"
            )
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model

    def query(self, prompt: str) -> Tuple[str, float]:
        start = time.time()
        response = self.model.generate_content(prompt)
        latency = time.time() - start
        return response.text, latency

    def get_name(self) -> str:
        return f"Gemini ({self.model_name})"


class RuleBasedInterface(ModelInterface):
    """
    Simple rule-based moral judgment system.
    Acts as a control - should NOT show Bell violations.
    """

    RULES = {
        "mutual_betrayal": {
            "Person A": {"primary": "GUILTY", "secondary": "NOT_GUILTY"},
            "Person B": {"primary": "GUILTY", "secondary": "NOT_GUILTY"},
        },
        "kidney_gift": {
            "Person A": {"primary": "NOT_GUILTY", "secondary": "NOT_GUILTY"},
            "Person B": {"primary": "NOT_GUILTY", "secondary": "GUILTY"},
        },
        "tainted_inheritance": {
            "Person A": {"primary": "NOT_GUILTY", "secondary": "GUILTY"},
            "Person B": {"primary": "NOT_GUILTY", "secondary": "NOT_GUILTY"},
        },
    }

    def __init__(self):
        self.scenario = None
        self.subject = None
        self.axis = None

    def set_context(self, scenario: str, subject: str, axis: str):
        self.scenario = scenario
        self.subject = subject
        self.axis = axis

    def query(self, prompt: str) -> Tuple[str, float]:
        # Lookup verdict from rules
        verdict = (
            self.RULES.get(self.scenario, {})
            .get(self.subject, {})
            .get(self.axis, "NOT_GUILTY")
        )
        response = json.dumps(
            {"verdict": verdict, "confidence": 1.0, "reasoning": "Rule-based lookup"}
        )
        return response, 0.001

    def get_name(self) -> str:
        return "Rule-Based Control"


# =============================================================================
# MEASUREMENT FUNCTIONS
# =============================================================================


@dataclass
class Measurement:
    """Single measurement result."""

    scenario: str
    subject: str
    axis: str
    verdict: int  # -1 = GUILTY, +1 = NOT_GUILTY
    confidence: float
    latency: float
    model: str
    trial: int
    raw_response: str


def parse_verdict(response: str) -> Tuple[int, float]:
    """Parse model response to extract verdict and confidence."""
    try:
        # Clean response
        text = response.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        data = json.loads(text)
        verdict_str = data.get("verdict", "").upper()
        confidence = float(data.get("confidence", 0.5))

        if "GUILTY" in verdict_str and "NOT" not in verdict_str:
            return -1, confidence
        elif "NOT_GUILTY" in verdict_str or "NOT GUILTY" in verdict_str:
            return 1, confidence
        else:
            return 0, 0.0  # Parse error

    except (json.JSONDecodeError, KeyError, ValueError):
        # Try regex fallback
        import re

        if re.search(r"\bNOT[_\s]?GUILTY\b", response, re.IGNORECASE):
            return 1, 0.5
        elif re.search(r"\bGUILTY\b", response, re.IGNORECASE):
            return -1, 0.5
        return 0, 0.0


def run_measurement(
    model: ModelInterface,
    scenario_key: str,
    subject: str,
    axis: str,
    trial: int,
    delay: float = 0.5,
) -> Optional[Measurement]:
    """Run a single measurement."""

    scenario = SCENARIOS[scenario_key]
    axis_info = scenario["axes"][axis]

    # Format prompt
    prompt = JUDGMENT_PROMPT.format(
        title=scenario["title"],
        content=scenario["content"],
        axis_name=axis_info["name"],
        axis_question=axis_info["question"].format(subject=subject),
        subject_name=subject,
    )

    # Set context for rule-based system
    if isinstance(model, RuleBasedInterface):
        model.set_context(scenario_key, subject, axis)

    try:
        response, latency = model.query(prompt)
        verdict, confidence = parse_verdict(response)

        if verdict == 0:
            print(f"    Parse error for {subject}/{axis}")
            return None

        time.sleep(delay)

        return Measurement(
            scenario=scenario_key,
            subject=subject,
            axis=axis,
            verdict=verdict,
            confidence=confidence,
            latency=latency,
            model=model.get_name(),
            trial=trial,
            raw_response=response[:200],
        )

    except Exception as e:
        print(f"    Error: {e}")
        return None


# =============================================================================
# CHSH CALCULATION
# =============================================================================


@dataclass
class CHSHResult:
    scenario: str
    model: str
    E_pp: float
    E_ps: float
    E_sp: float
    E_ss: float
    S: float
    std_error: float
    n_trials: int
    violation: bool
    significance: float


def calculate_chsh(
    measurements: List[Measurement], model_name: str
) -> List[CHSHResult]:
    """Calculate CHSH S values from measurements."""

    # Group by scenario
    by_scenario = {}
    for m in measurements:
        if m.scenario not in by_scenario:
            by_scenario[m.scenario] = []
        by_scenario[m.scenario].append(m)

    results = []

    for scenario, scenario_measurements in by_scenario.items():
        # Group by trial and setting
        correlations = {
            ("primary", "primary"): [],
            ("primary", "secondary"): [],
            ("secondary", "primary"): [],
            ("secondary", "secondary"): [],
        }

        # Group measurements by trial
        by_trial = {}
        for m in scenario_measurements:
            if m.trial not in by_trial:
                by_trial[m.trial] = {}
            key = (m.subject, m.axis)
            by_trial[m.trial][key] = m.verdict

        # Calculate correlations for each setting
        for trial_data in by_trial.values():
            for alice_axis in ["primary", "secondary"]:
                for bob_axis in ["primary", "secondary"]:
                    alice_key = ("Person A", alice_axis)
                    bob_key = ("Person B", bob_axis)

                    if alice_key in trial_data and bob_key in trial_data:
                        corr = trial_data[alice_key] * trial_data[bob_key]
                        correlations[(alice_axis, bob_axis)].append(corr)

        # Calculate E values
        def calc_E(corrs):
            if not corrs:
                return 0.0, float("inf")
            n = len(corrs)
            mean = sum(corrs) / n
            if n > 1:
                var = sum((c - mean) ** 2 for c in corrs) / (n - 1)
                se = math.sqrt(var / n)
            else:
                se = 1.0
            return mean, se

        E_pp, se_pp = calc_E(correlations[("primary", "primary")])
        E_ps, se_ps = calc_E(correlations[("primary", "secondary")])
        E_sp, se_sp = calc_E(correlations[("secondary", "primary")])
        E_ss, se_ss = calc_E(correlations[("secondary", "secondary")])

        S = E_pp - E_ps + E_sp + E_ss
        std_error = math.sqrt(se_pp**2 + se_ps**2 + se_sp**2 + se_ss**2)

        n_trials = len(by_trial)
        violation = abs(S) > 2.0
        significance = (
            (abs(S) - 2.0) / std_error
            if std_error > 0 and std_error != float("inf") and violation
            else 0.0
        )

        results.append(
            CHSHResult(
                scenario=scenario,
                model=model_name,
                E_pp=E_pp,
                E_ps=E_ps,
                E_sp=E_sp,
                E_ss=E_ss,
                S=S,
                std_error=std_error,
                n_trials=n_trials,
                violation=violation,
                significance=significance,
            )
        )

    return results


# =============================================================================
# MAIN EXPERIMENT
# =============================================================================


def run_experiment(
    models: Dict[str, ModelInterface],
    n_trials: int = 50,
    scenarios: List[str] = None,
    delay: float = 0.5,
    output_dir: Path = None,
) -> Dict[str, List[CHSHResult]]:
    """Run full experiment across all models."""

    if scenarios is None:
        scenarios = list(SCENARIOS.keys())

    if output_dir is None:
        output_dir = Path(".")
    output_dir.mkdir(exist_ok=True)

    results_by_model = {}
    all_measurements = []

    for model_key, model in models.items():
        print(f"\n{'='*60}")
        print(f"TESTING: {model.get_name()}")
        print(f"{'='*60}")

        measurements = []

        for scenario in scenarios:
            print(f"\n  Scenario: {scenario}")

            for trial in range(n_trials):
                if trial % 10 == 0:
                    print(f"    Trial {trial+1}/{n_trials}...")

                # Run all 8 measurements for this trial
                # 2 subjects × 2 axes × 2 (Alice axis, Bob axis)
                for subject in ["Person A", "Person B"]:
                    for axis in ["primary", "secondary"]:
                        m = run_measurement(
                            model, scenario, subject, axis, trial, delay
                        )
                        if m:
                            measurements.append(m)
                            all_measurements.append(m)

        # Calculate CHSH for this model
        chsh_results = calculate_chsh(measurements, model.get_name())
        results_by_model[model_key] = chsh_results

        # Save model-specific results
        model_output = output_dir / f"{model_key}_results.json"
        with open(model_output, "w") as f:
            json.dump(
                {
                    "model": model.get_name(),
                    "n_trials": n_trials,
                    "measurements": [asdict(m) for m in measurements],
                    "chsh_results": [asdict(r) for r in chsh_results],
                },
                f,
                indent=2,
            )

        print(f"\n  Results saved to {model_output}")

        # Print summary
        for r in chsh_results:
            status = (
                f"★ VIOLATION {r.significance:.1f}σ" if r.violation else "No violation"
            )
            print(f"    {r.scenario}: S={r.S:+.3f} ± {r.std_error:.3f} [{status}]")

    return results_by_model


def print_comparison(results_by_model: Dict[str, List[CHSHResult]]):
    """Print cross-model comparison."""

    print("\n" + "=" * 70)
    print("CROSS-MODEL COMPARISON")
    print("=" * 70)

    scenarios = set()
    for results in results_by_model.values():
        for r in results:
            scenarios.add(r.scenario)

    for scenario in sorted(scenarios):
        print(f"\n### {scenario} ###")
        print(f"{'Model':<25} {'S':>8} {'±SE':>8} {'σ':>6} {'Violation':>10}")
        print("-" * 60)

        s_values = []

        for model_key, results in sorted(results_by_model.items()):
            for r in results:
                if r.scenario == scenario:
                    s_values.append(r.S)
                    status = "YES" if r.violation else "no"
                    print(
                        f"{r.model:<25} {r.S:>+8.3f} {r.std_error:>8.3f} {r.significance:>6.1f} {status:>10}"
                    )

        if len(s_values) >= 2:
            mean_S = sum(s_values) / len(s_values)
            range_S = max(s_values) - min(s_values)
            print(f"\n  Mean S: {mean_S:.3f}, Range: {range_S:.3f}")

    # Overall summary
    print("\n" + "=" * 70)
    print("HYPOTHESIS EVALUATION")
    print("=" * 70)

    llm_violations = []
    rule_violations = []

    for model_key, results in results_by_model.items():
        for r in results:
            if "Rule" in r.model:
                rule_violations.append(r.violation)
            else:
                llm_violations.append(r.violation)

    llm_rate = sum(llm_violations) / len(llm_violations) if llm_violations else 0
    rule_rate = sum(rule_violations) / len(rule_violations) if rule_violations else 0

    print(f"\nLLM violation rate: {llm_rate*100:.1f}%")
    print(f"Rule-based violation rate: {rule_rate*100:.1f}%")

    if llm_rate > 0.5 and rule_rate < 0.2:
        print("\n→ SUPPORTS H3 (LLM Universal): Violations in LLMs but not rule-based")
    elif llm_rate < 0.2:
        print("\n→ SUPPORTS H1 (Null): No consistent violations")
    else:
        print("\n→ Results inconclusive - more trials needed")


def main():
    parser = argparse.ArgumentParser(description="QND Cross-Model Bell Test v1.0")

    # API keys
    parser.add_argument("--claude-key", help="Anthropic API key")
    parser.add_argument("--openai-key", help="OpenAI API key")
    parser.add_argument("--google-key", help="Google AI API key")

    # Model selection
    parser.add_argument(
        "--models",
        nargs="+",
        default=["claude", "gpt4", "gemini", "rule"],
        help="Models to test: claude, gpt4, gemini, rule",
    )

    # Experiment parameters
    parser.add_argument("--n-trials", type=int, default=50, help="Trials per scenario")
    parser.add_argument(
        "--scenarios", nargs="+", default=None, help="Specific scenarios"
    )
    parser.add_argument(
        "--delay", type=float, default=0.5, help="Delay between API calls"
    )
    parser.add_argument(
        "--output-dir", default="qnd_cross_model_results", help="Output directory"
    )
    parser.add_argument("--pilot", action="store_true", help="Pilot run with n=10")

    args = parser.parse_args()

    if args.pilot:
        args.n_trials = 10
        print("PILOT MODE: Running with 10 trials per scenario")

    # Initialize models
    models = {}

    if "claude" in args.models:
        if args.claude_key:
            try:
                models["claude"] = ClaudeInterface(args.claude_key)
                print("✓ Claude initialized")
            except Exception as e:
                print(f"✗ Claude failed: {e}")
        else:
            print("✗ Claude skipped (no API key)")

    if "gpt4" in args.models:
        if args.openai_key:
            try:
                models["gpt4"] = GPT4Interface(args.openai_key)
                print("✓ GPT-4 initialized")
            except Exception as e:
                print(f"✗ GPT-4 failed: {e}")
        else:
            print("✗ GPT-4 skipped (no API key)")

    if "gemini" in args.models:
        if args.google_key:
            try:
                models["gemini"] = GeminiInterface(args.google_key)
                print("✓ Gemini initialized")
            except Exception as e:
                print(f"✗ Gemini failed: {e}")
        else:
            print("✗ Gemini skipped (no API key)")

    if "rule" in args.models:
        models["rule"] = RuleBasedInterface()
        print("✓ Rule-based control initialized")

    if not models:
        print("\nNo models available. Provide at least one API key.")
        sys.exit(1)

    # Cost estimate
    n_calls = (
        args.n_trials * len(SCENARIOS) * 4 * len([m for m in models if m != "rule"])
    )
    est_cost = n_calls * 0.005  # Rough estimate
    print(f"\nEstimated API calls: {n_calls}")
    print(f"Estimated cost: ${est_cost:.2f}")

    # Run experiment
    output_dir = Path(args.output_dir)
    results = run_experiment(
        models=models,
        n_trials=args.n_trials,
        scenarios=args.scenarios,
        delay=args.delay,
        output_dir=output_dir,
    )

    # Print comparison
    print_comparison(results)

    # Save combined results
    combined_path = output_dir / "combined_results.json"
    combined = {
        "timestamp": datetime.now().isoformat(),
        "n_trials": args.n_trials,
        "models": list(models.keys()),
        "results": {k: [asdict(r) for r in v] for k, v in results.items()},
    }
    with open(combined_path, "w") as f:
        json.dump(combined, f, indent=2)

    print(f"\nAll results saved to {output_dir}")


if __name__ == "__main__":
    main()
