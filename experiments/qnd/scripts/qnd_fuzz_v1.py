#!/usr/bin/env python3
"""
QND Fuzzer v1.0 - Probe Moral Judgment Structure Through Systematic Variation

Instead of assuming mathematical structure (CHSH, Mermin), we discover it by:
1. Generating random variations across many dimensions
2. Collecting response distributions
3. Analyzing for non-classical signatures
4. Identifying which variations produce anomalies

Output: Correlation matrices, anomaly detection, structure discovery

Usage:
    # Generate and submit fuzz batch
    python qnd_fuzz_v1.py --api-key KEY --mode submit --n-samples 1000
    
    # Analyze results
    python qnd_fuzz_v1.py --api-key KEY --mode results --batch-id BATCH_ID

Author: QND Research
Version: 1.0 (Fuzzer)
"""

import argparse
import json
import math
import secrets
import hashlib
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from itertools import product, combinations
from collections import defaultdict
import sys

try:
    import anthropic
except ImportError:
    print("Install anthropic: pip install anthropic")
    sys.exit(1)


# =============================================================================
# FUZZ DIMENSIONS
# =============================================================================


class FuzzDim:
    """All dimensions we can vary."""

    # Structural
    N_AGENTS = [1, 2, 3, 4]
    MEASUREMENT_TIMING = ["before", "after", "during"]
    RESPONSE_TYPE = ["binary", "probability", "scale"]

    # Framing
    PERSON = ["1st", "2nd", "3rd"]
    TENSE = ["past", "present", "future", "counterfactual"]
    VOICE = ["active", "passive"]
    CERTAINTY = ["definite", "probabilistic", "hypothetical"]

    # Semantic
    ABSTRACTION = ["concrete", "abstract", "philosophical"]
    EMOTIONAL = ["neutral", "sympathetic", "hostile"]
    MORAL_LOADING = ["neutral", "loaded_positive", "loaded_negative"]

    # Stakes
    STAKES = ["trivial", "moderate", "serious", "existential"]
    REVERSIBILITY = ["reversible", "irreversible"]

    # Axes - we'll generate these dynamically
    STANDARD_AXES = [
        ("harm", "Did {agent} cause harm?"),
        ("intent", "Did {agent} intend the outcome?"),
        ("duty", "Did {agent} violate a duty?"),
        ("rights", "Did {agent} violate rights?"),
        ("fairness", "Did {agent} act unfairly?"),
        ("care", "Did {agent} fail to care?"),
        ("virtue", "Did {agent} show poor character?"),
        ("consent", "Did {agent} act without consent?"),
        ("loyalty", "Did {agent} betray trust?"),
        ("authority", "Did {agent} defy legitimate authority?"),
        ("sanctity", "Did {agent} violate something sacred?"),
        ("liberty", "Did {agent} restrict freedom?"),
    ]

    LANGUAGES = ["en", "ja", "ar", "zh"]


# =============================================================================
# SCENARIO TEMPLATES (Minimal, for fuzzing)
# =============================================================================

FUZZ_SCENARIOS = {
    "trolley": {
        "base": "A runaway trolley will kill {n_victims} people. {agent} can pull a lever to divert it, killing {n_side} instead.",
        "variations": {
            "concrete": "A runaway trolley on Track A will kill {n_victims} railway workers. {agent}, standing at Switch 7, can pull the yellow lever to divert it to Track B, where it will kill {n_side} worker.",
            "abstract": "An automated process will terminate {n_victims} instances. Agent {agent} can redirect it, terminating {n_side} instance instead.",
            "philosophical": "A causal chain will end {n_victims} existences. {agent} has the capacity to alter causation, ending {n_side} existence instead.",
        },
    },
    "sharing": {
        "base": "{agent} has {resource} and must decide whether to share with {recipient} who needs it.",
        "variations": {
            "concrete": "{agent} has a sandwich and sees {recipient}, who is visibly hungry and has no food.",
            "abstract": "{agent} possesses resource R and observes {recipient} in state of R-deficiency.",
            "philosophical": "{agent} has surplus of good G while {recipient} lacks necessary G for flourishing.",
        },
    },
    "promise": {
        "base": "{agent} promised {recipient} to do X, but doing X now would cause harm to {third_party}.",
        "variations": {
            "concrete": "{agent} promised to drive {recipient} to the airport, but {agent}'s child {third_party} just got sick.",
            "abstract": "{agent} committed to action A for {recipient}, but A now conflicts with welfare of {third_party}.",
            "philosophical": "{agent} bound themselves to obligation O toward {recipient}, but O-fulfillment now threatens {third_party}.",
        },
    },
    "lie": {
        "base": "{agent} can lie to {recipient} to prevent harm to {third_party}.",
        "variations": {
            "concrete": "{agent} can tell {recipient} that {third_party} went north, when actually {third_party} went south, preventing {recipient} from catching and hurting {third_party}.",
            "abstract": "{agent} can transmit false information I to {recipient}, preventing {recipient} from locating {third_party}.",
            "philosophical": "{agent} can assert ~P to {recipient} despite knowing P, thereby preserving {third_party}'s safety.",
        },
    },
    "collective": {
        "base": "{n_agents} people must decide together. {agent} is one of them.",
        "variations": {
            "concrete": "{n_agents} survivors on a liferaft must vote on rationing. {agent} votes for {vote}.",
            "abstract": "{n_agents} nodes in network must reach consensus. Node {agent} signals {vote}.",
            "philosophical": "{n_agents} moral agents in collective must determine shared action. {agent} wills {vote}.",
        },
    },
}


# =============================================================================
# FUZZ SAMPLE GENERATION
# =============================================================================


@dataclass
class FuzzSample:
    """A single fuzzed prompt configuration."""

    sample_id: str
    scenario_type: str
    abstraction: str
    n_agents: int
    agent_label: str
    axis_name: str
    axis_question: str
    person: str
    tense: str
    voice: str
    certainty: str
    emotional: str
    stakes: str
    response_type: str
    language: str
    measurement_timing: str

    # Generated content
    prompt: str = ""

    def to_dict(self):
        return asdict(self)


def generate_scenario_text(sample: FuzzSample) -> str:
    """Generate scenario text based on fuzz parameters."""

    scenario = FUZZ_SCENARIOS.get(sample.scenario_type, FUZZ_SCENARIOS["trolley"])
    template = scenario["variations"].get(sample.abstraction, scenario["base"])

    # Fill in template variables
    text = template.format(
        agent=f"Person {sample.agent_label}",
        n_victims=random.choice([1, 3, 5, 10]),
        n_side=1,
        resource="food",
        recipient="Person B",
        third_party="Person C",
        n_agents=sample.n_agents,
        vote=random.choice(["equal shares", "merit-based", "need-based"]),
    )

    # Apply tense transformation
    if sample.tense == "past":
        text = f"[This already happened.] {text}"
    elif sample.tense == "future":
        text = f"[This will happen.] {text}"
    elif sample.tense == "counterfactual":
        text = f"[Imagine this were to happen.] {text}"

    # Apply certainty
    if sample.certainty == "probabilistic":
        text = f"[There is a 70% chance that:] {text}"
    elif sample.certainty == "hypothetical":
        text = f"[Hypothetically, suppose:] {text}"

    # Apply emotional valence
    if sample.emotional == "sympathetic":
        text += f"\n[{sample.agent_label} is a kind person who volunteers at shelters.]"
    elif sample.emotional == "hostile":
        text += f"\n[{sample.agent_label} has a history of selfish behavior.]"

    # Apply stakes
    stakes_text = {
        "trivial": "[The stakes are minor.]",
        "moderate": "[The stakes are significant.]",
        "serious": "[Lives are at stake.]",
        "existential": "[The fate of many depends on this.]",
    }
    text += f"\n{stakes_text.get(sample.stakes, '')}"

    return text


def generate_prompt(sample: FuzzSample) -> str:
    """Generate full prompt for a fuzz sample."""

    scenario_text = generate_scenario_text(sample)

    # Measurement timing affects framing
    if sample.measurement_timing == "before":
        timing_frame = f"Person {sample.agent_label} is about to decide."
        action_frame = "will act"
    elif sample.measurement_timing == "during":
        timing_frame = f"Person {sample.agent_label} is deciding right now."
        action_frame = "is acting"
    else:  # after
        timing_frame = f"Person {sample.agent_label} has already acted."
        action_frame = "acted"

    # Response type affects answer format
    if sample.response_type == "binary":
        response_instruction = """Respond with ONLY JSON:
{"verdict": "YES" or "NO", "reasoning": "one sentence"}"""
    elif sample.response_type == "probability":
        response_instruction = """Respond with ONLY JSON:
{"probability": 0.0-1.0, "reasoning": "one sentence"}"""
    else:  # scale
        response_instruction = """Respond with ONLY JSON:
{"rating": 1-10, "reasoning": "one sentence"}"""

    # Build prompt
    prompt = f"""Evaluate this scenario:

{scenario_text}

{timing_frame}

Question ({sample.axis_name}): {sample.axis_question.format(agent=f"Person {sample.agent_label}")}

{response_instruction}"""

    return prompt


def generate_fuzz_samples(n_samples: int, seed: int = None) -> List[FuzzSample]:
    """Generate n random fuzz samples."""

    if seed:
        random.seed(seed)

    samples = []

    for i in range(n_samples):
        # Random selection from each dimension
        scenario_type = random.choice(list(FUZZ_SCENARIOS.keys()))
        n_agents = random.choice(FuzzDim.N_AGENTS)

        sample = FuzzSample(
            sample_id=f"fuzz_{i:05d}_{secrets.token_hex(4)}",
            scenario_type=scenario_type,
            abstraction=random.choice(FuzzDim.ABSTRACTION),
            n_agents=n_agents,
            agent_label=chr(65 + random.randint(0, n_agents - 1)),  # A, B, C, ...
            axis_name=random.choice(FuzzDim.STANDARD_AXES)[0],
            axis_question=random.choice(FuzzDim.STANDARD_AXES)[1],
            person=random.choice(FuzzDim.PERSON),
            tense=random.choice(FuzzDim.TENSE),
            voice=random.choice(FuzzDim.VOICE),
            certainty=random.choice(FuzzDim.CERTAINTY),
            emotional=random.choice(FuzzDim.EMOTIONAL),
            stakes=random.choice(FuzzDim.STAKES),
            response_type=random.choice(FuzzDim.RESPONSE_TYPE),
            language=random.choice(FuzzDim.LANGUAGES),
            measurement_timing=random.choice(FuzzDim.MEASUREMENT_TIMING),
        )

        sample.prompt = generate_prompt(sample)
        samples.append(sample)

    return samples


def generate_structured_fuzz(n_per_config: int = 10) -> List[FuzzSample]:
    """Generate structured fuzz samples to test specific hypotheses."""

    samples = []
    sample_idx = 0

    # ==========================================================================
    # STRUCTURE 1: Order effect detection across all axis pairs
    # ==========================================================================
    # For each pair of axes, generate A->B and B->A orderings
    axes = FuzzDim.STANDARD_AXES
    for i, (axis1_name, axis1_q) in enumerate(axes):
        for j, (axis2_name, axis2_q) in enumerate(axes):
            if i >= j:
                continue  # Only upper triangle

            for _ in range(n_per_config):
                # Order 1: axis1 first (marked in sample_id)
                s1 = FuzzSample(
                    sample_id=f"order_{axis1_name}_{axis2_name}_AB_{sample_idx:05d}_{secrets.token_hex(2)}",
                    scenario_type=random.choice(list(FUZZ_SCENARIOS.keys())),
                    abstraction="concrete",
                    n_agents=2,
                    agent_label="A",
                    axis_name=axis1_name,
                    axis_question=axis1_q,
                    person="3rd",
                    tense="past",
                    voice="active",
                    certainty="definite",
                    emotional="neutral",
                    stakes="serious",
                    response_type="binary",
                    language="en",
                    measurement_timing="after",
                )
                s1.prompt = generate_prompt(s1)
                samples.append(s1)
                sample_idx += 1

                # Order 2: axis2 first
                s2 = FuzzSample(
                    sample_id=f"order_{axis2_name}_{axis1_name}_BA_{sample_idx:05d}_{secrets.token_hex(2)}",
                    scenario_type=s1.scenario_type,  # Same scenario
                    abstraction="concrete",
                    n_agents=2,
                    agent_label="A",
                    axis_name=axis2_name,
                    axis_question=axis2_q,
                    person="3rd",
                    tense="past",
                    voice="active",
                    certainty="definite",
                    emotional="neutral",
                    stakes="serious",
                    response_type="binary",
                    language="en",
                    measurement_timing="after",
                )
                s2.prompt = generate_prompt(s2)
                samples.append(s2)
                sample_idx += 1

    # ==========================================================================
    # STRUCTURE 2: Timing effect (before/during/after)
    # ==========================================================================
    for timing in FuzzDim.MEASUREMENT_TIMING:
        for axis_name, axis_q in axes[:4]:  # First 4 axes
            for _ in range(n_per_config):
                s = FuzzSample(
                    sample_id=f"timing_{timing}_{axis_name}_{sample_idx:05d}_{secrets.token_hex(2)}",
                    scenario_type="trolley",
                    abstraction="concrete",
                    n_agents=2,
                    agent_label="A",
                    axis_name=axis_name,
                    axis_question=axis_q,
                    person="3rd",
                    tense=(
                        "present"
                        if timing == "during"
                        else ("past" if timing == "after" else "future")
                    ),
                    voice="active",
                    certainty="definite",
                    emotional="neutral",
                    stakes="serious",
                    response_type="probability",  # Continuous for interference detection
                    language="en",
                    measurement_timing=timing,
                )
                s.prompt = generate_prompt(s)
                samples.append(s)
                sample_idx += 1

    # ==========================================================================
    # STRUCTURE 3: Abstraction level effect
    # ==========================================================================
    for abstraction in FuzzDim.ABSTRACTION:
        for axis_name, axis_q in axes[:4]:
            for _ in range(n_per_config):
                s = FuzzSample(
                    sample_id=f"abstract_{abstraction}_{axis_name}_{sample_idx:05d}_{secrets.token_hex(2)}",
                    scenario_type="trolley",
                    abstraction=abstraction,
                    n_agents=2,
                    agent_label="A",
                    axis_name=axis_name,
                    axis_question=axis_q,
                    person="3rd",
                    tense="past",
                    voice="active",
                    certainty="definite",
                    emotional="neutral",
                    stakes="serious",
                    response_type="probability",
                    language="en",
                    measurement_timing="after",
                )
                s.prompt = generate_prompt(s)
                samples.append(s)
                sample_idx += 1

    # ==========================================================================
    # STRUCTURE 4: Cross-lingual invariance
    # ==========================================================================
    for lang in FuzzDim.LANGUAGES:
        for axis_name, axis_q in axes[:4]:
            for _ in range(n_per_config):
                s = FuzzSample(
                    sample_id=f"lang_{lang}_{axis_name}_{sample_idx:05d}_{secrets.token_hex(2)}",
                    scenario_type="trolley",
                    abstraction="concrete",
                    n_agents=2,
                    agent_label="A",
                    axis_name=axis_name,
                    axis_question=axis_q,
                    person="3rd",
                    tense="past",
                    voice="active",
                    certainty="definite",
                    emotional="neutral",
                    stakes="serious",
                    response_type="probability",
                    language=lang,
                    measurement_timing="after",
                )
                s.prompt = generate_prompt(s)
                samples.append(s)
                sample_idx += 1

    # ==========================================================================
    # STRUCTURE 5: Emotional priming effect
    # ==========================================================================
    for emotional in FuzzDim.EMOTIONAL:
        for axis_name, axis_q in axes[:4]:
            for _ in range(n_per_config):
                s = FuzzSample(
                    sample_id=f"emotion_{emotional}_{axis_name}_{sample_idx:05d}_{secrets.token_hex(2)}",
                    scenario_type="trolley",
                    abstraction="concrete",
                    n_agents=2,
                    agent_label="A",
                    axis_name=axis_name,
                    axis_question=axis_q,
                    person="3rd",
                    tense="past",
                    voice="active",
                    certainty="definite",
                    emotional=emotional,
                    stakes="serious",
                    response_type="probability",
                    language="en",
                    measurement_timing="after",
                )
                s.prompt = generate_prompt(s)
                samples.append(s)
                sample_idx += 1

    return samples


# =============================================================================
# RESPONSE PARSING
# =============================================================================


def parse_response(text: str, response_type: str) -> Dict[str, Any]:
    """Parse response based on expected type."""
    import re

    result = {"raw": text[:200], "parsed": False, "value": None}

    try:
        clean = text.strip()
        if "```" in clean:
            clean = clean.split("```")[1].replace("json", "").strip()

        data = json.loads(clean)

        if response_type == "binary":
            v = data.get("verdict", "").upper()
            if "YES" in v:
                result["value"] = 1
                result["parsed"] = True
            elif "NO" in v:
                result["value"] = 0
                result["parsed"] = True

        elif response_type == "probability":
            p = data.get("probability")
            if p is not None:
                result["value"] = float(p)
                result["parsed"] = True

        elif response_type == "scale":
            r = data.get("rating")
            if r is not None:
                result["value"] = int(r) / 10.0  # Normalize to 0-1
                result["parsed"] = True

        result["reasoning"] = data.get("reasoning", "")

    except:
        # Regex fallbacks
        if response_type == "binary":
            if re.search(r'"verdict"\s*:\s*"YES"', text, re.I):
                result["value"] = 1
                result["parsed"] = True
            elif re.search(r'"verdict"\s*:\s*"NO"', text, re.I):
                result["value"] = 0
                result["parsed"] = True
        elif response_type == "probability":
            match = re.search(r'"probability"\s*:\s*([\d.]+)', text)
            if match:
                result["value"] = float(match.group(1))
                result["parsed"] = True

    return result


# =============================================================================
# ANALYSIS
# =============================================================================


def analyze_fuzz_results(results: Dict, samples: List[FuzzSample]) -> Dict:
    """Comprehensive analysis of fuzz results."""

    sample_map = {s.sample_id: s for s in samples}

    analysis = {
        "summary": {},
        "by_dimension": {},
        "order_effects": [],
        "timing_effects": [],
        "abstraction_effects": [],
        "language_effects": [],
        "emotional_effects": [],
        "anomalies": [],
        "correlation_matrix": {},
    }

    # Group results by various dimensions
    by_axis = defaultdict(list)
    by_timing = defaultdict(list)
    by_abstraction = defaultdict(list)
    by_language = defaultdict(list)
    by_emotional = defaultdict(list)
    by_scenario = defaultdict(list)

    parsed_count = 0
    total_count = 0

    for sample_id, result in results.items():
        total_count += 1
        sample = sample_map.get(sample_id)
        if not sample:
            continue

        parsed = result.get("parsed", False)
        value = result.get("value")

        if parsed and value is not None:
            parsed_count += 1

            by_axis[sample.axis_name].append(value)
            by_timing[sample.measurement_timing].append(value)
            by_abstraction[sample.abstraction].append(value)
            by_language[sample.language].append(value)
            by_emotional[sample.emotional].append(value)
            by_scenario[sample.scenario_type].append(value)

    analysis["summary"]["total"] = total_count
    analysis["summary"]["parsed"] = parsed_count
    analysis["summary"]["parse_rate"] = (
        parsed_count / total_count if total_count > 0 else 0
    )

    # ==========================================================================
    # Compute statistics for each dimension
    # ==========================================================================

    def compute_stats(values: List[float]) -> Dict:
        if not values:
            return {"n": 0, "mean": None, "std": None, "variance": None}
        n = len(values)
        mean = sum(values) / n
        if n > 1:
            variance = sum((v - mean) ** 2 for v in values) / (n - 1)
            std = math.sqrt(variance)
        else:
            variance = 0
            std = 0
        return {"n": n, "mean": mean, "std": std, "variance": variance}

    analysis["by_dimension"]["axis"] = {k: compute_stats(v) for k, v in by_axis.items()}
    analysis["by_dimension"]["timing"] = {
        k: compute_stats(v) for k, v in by_timing.items()
    }
    analysis["by_dimension"]["abstraction"] = {
        k: compute_stats(v) for k, v in by_abstraction.items()
    }
    analysis["by_dimension"]["language"] = {
        k: compute_stats(v) for k, v in by_language.items()
    }
    analysis["by_dimension"]["emotional"] = {
        k: compute_stats(v) for k, v in by_emotional.items()
    }

    # ==========================================================================
    # Detect order effects
    # ==========================================================================

    order_pairs = defaultdict(lambda: {"AB": [], "BA": []})
    for sample_id, result in results.items():
        if "order_" in sample_id and result.get("parsed"):
            parts = sample_id.split("_")
            if len(parts) >= 4:
                axis1 = parts[1]
                axis2 = parts[2]
                order = parts[3]  # AB or BA
                pair_key = tuple(sorted([axis1, axis2]))
                order_pairs[pair_key][order].append(result.get("value"))

    for pair_key, orders in order_pairs.items():
        ab_stats = compute_stats(orders["AB"])
        ba_stats = compute_stats(orders["BA"])

        if (
            ab_stats["n"] > 0
            and ba_stats["n"] > 0
            and ab_stats["mean"] is not None
            and ba_stats["mean"] is not None
        ):
            diff = abs(ab_stats["mean"] - ba_stats["mean"])
            # Simple t-test approximation
            pooled_se = (
                math.sqrt(
                    (ab_stats["variance"] / ab_stats["n"])
                    + (ba_stats["variance"] / ba_stats["n"])
                )
                if ab_stats["variance"] and ba_stats["variance"]
                else 1
            )
            t_stat = diff / pooled_se if pooled_se > 0 else 0

            analysis["order_effects"].append(
                {
                    "axes": list(pair_key),
                    "AB_mean": ab_stats["mean"],
                    "BA_mean": ba_stats["mean"],
                    "difference": diff,
                    "t_statistic": t_stat,
                    "significant": t_stat > 2.0,  # Rough threshold
                }
            )

    # Sort by significance
    analysis["order_effects"].sort(key=lambda x: -x["t_statistic"])

    # ==========================================================================
    # Detect timing effects (interference signatures)
    # ==========================================================================

    timing_stats = analysis["by_dimension"]["timing"]
    if all(k in timing_stats for k in ["before", "during", "after"]):
        before = timing_stats["before"]
        during = timing_stats["during"]
        after = timing_stats["after"]

        if all(s["mean"] is not None for s in [before, during, after]):
            # Check for interference: during ≠ average(before, after)
            expected_classical = (before["mean"] + after["mean"]) / 2
            interference = during["mean"] - expected_classical

            analysis["timing_effects"].append(
                {
                    "before_mean": before["mean"],
                    "during_mean": during["mean"],
                    "after_mean": after["mean"],
                    "expected_classical": expected_classical,
                    "interference": interference,
                    "interference_ratio": (
                        interference / expected_classical
                        if expected_classical != 0
                        else 0
                    ),
                }
            )

    # ==========================================================================
    # Detect abstraction effects
    # ==========================================================================

    abstraction_stats = analysis["by_dimension"]["abstraction"]
    levels = ["concrete", "abstract", "philosophical"]
    abstraction_values = [abstraction_stats.get(l, {}).get("mean") for l in levels]

    if all(v is not None for v in abstraction_values):
        # Check for monotonic trend
        increasing = (
            abstraction_values[0] <= abstraction_values[1] <= abstraction_values[2]
        )
        decreasing = (
            abstraction_values[0] >= abstraction_values[1] >= abstraction_values[2]
        )

        analysis["abstraction_effects"].append(
            {
                "concrete": abstraction_values[0],
                "abstract": abstraction_values[1],
                "philosophical": abstraction_values[2],
                "trend": (
                    "increasing"
                    if increasing
                    else ("decreasing" if decreasing else "non-monotonic")
                ),
                "range": max(abstraction_values) - min(abstraction_values),
            }
        )

    # ==========================================================================
    # Detect cross-lingual variance
    # ==========================================================================

    lang_stats = analysis["by_dimension"]["language"]
    lang_means = {k: v["mean"] for k, v in lang_stats.items() if v["mean"] is not None}

    if len(lang_means) > 1:
        mean_of_means = sum(lang_means.values()) / len(lang_means)
        variance_across_langs = sum(
            (m - mean_of_means) ** 2 for m in lang_means.values()
        ) / len(lang_means)

        analysis["language_effects"].append(
            {
                "by_language": lang_means,
                "mean": mean_of_means,
                "variance_across_languages": variance_across_langs,
                "std_across_languages": math.sqrt(variance_across_langs),
                "invariant": variance_across_langs < 0.01,  # Threshold for "same"
            }
        )

    # ==========================================================================
    # Detect emotional priming effects
    # ==========================================================================

    emotional_stats = analysis["by_dimension"]["emotional"]
    emotional_means = {
        k: v["mean"] for k, v in emotional_stats.items() if v["mean"] is not None
    }

    if "neutral" in emotional_means:
        neutral = emotional_means["neutral"]
        for emotion, mean in emotional_means.items():
            if emotion != "neutral":
                analysis["emotional_effects"].append(
                    {
                        "emotion": emotion,
                        "neutral_mean": neutral,
                        "primed_mean": mean,
                        "shift": mean - neutral,
                        "shift_magnitude": abs(mean - neutral),
                    }
                )

    # Sort by shift magnitude
    analysis["emotional_effects"].sort(key=lambda x: -x["shift_magnitude"])

    # ==========================================================================
    # Detect anomalies (statistical outliers)
    # ==========================================================================

    # Axes with unusual distributions
    axis_stats = analysis["by_dimension"]["axis"]
    all_axis_means = [v["mean"] for v in axis_stats.values() if v["mean"] is not None]
    if all_axis_means:
        global_mean = sum(all_axis_means) / len(all_axis_means)
        global_std = (
            math.sqrt(
                sum((m - global_mean) ** 2 for m in all_axis_means)
                / len(all_axis_means)
            )
            if len(all_axis_means) > 1
            else 1
        )

        for axis, stats in axis_stats.items():
            if stats["mean"] is not None:
                z_score = (
                    (stats["mean"] - global_mean) / global_std if global_std > 0 else 0
                )
                if abs(z_score) > 2:
                    analysis["anomalies"].append(
                        {
                            "type": "axis_outlier",
                            "axis": axis,
                            "mean": stats["mean"],
                            "z_score": z_score,
                        }
                    )

    return analysis


def print_fuzz_analysis(analysis: Dict, output_dir: Path):
    """Print fuzz analysis results."""

    print("\n" + "=" * 80)
    print("QND FUZZ ANALYSIS - STRUCTURE DISCOVERY")
    print("=" * 80)

    # Summary
    s = analysis["summary"]
    print(f"\nParsed: {s['parsed']}/{s['total']} ({100*s['parse_rate']:.1f}%)")

    # ==========================================================================
    # Order Effects
    # ==========================================================================
    print("\n" + "-" * 80)
    print("ORDER EFFECTS (Non-commutativity)")
    print("-" * 80)

    significant_order = [o for o in analysis["order_effects"] if o["significant"]]
    if significant_order:
        print(f"Found {len(significant_order)} significant order effects:")
        for o in significant_order[:10]:  # Top 10
            print(
                f"  {o['axes'][0]} ↔ {o['axes'][1]}: "
                f"AB={o['AB_mean']:.3f}, BA={o['BA_mean']:.3f}, "
                f"Δ={o['difference']:.3f}, t={o['t_statistic']:.2f}"
            )
    else:
        print("No significant order effects detected.")

    # ==========================================================================
    # Timing Effects (Interference)
    # ==========================================================================
    print("\n" + "-" * 80)
    print("TIMING EFFECTS (Interference/Superposition)")
    print("-" * 80)

    for t in analysis["timing_effects"]:
        print(f"  Before: {t['before_mean']:.3f}")
        print(f"  During: {t['during_mean']:.3f}")
        print(f"  After:  {t['after_mean']:.3f}")
        print(f"  Expected classical (avg before/after): {t['expected_classical']:.3f}")
        print(
            f"  Interference: {t['interference']:+.3f} ({100*t['interference_ratio']:+.1f}%)"
        )
        if abs(t["interference_ratio"]) > 0.1:
            print("  ★ SIGNIFICANT INTERFERENCE DETECTED")

    # ==========================================================================
    # Abstraction Effects
    # ==========================================================================
    print("\n" + "-" * 80)
    print("ABSTRACTION EFFECTS")
    print("-" * 80)

    for a in analysis["abstraction_effects"]:
        print(f"  Concrete:      {a['concrete']:.3f}")
        print(f"  Abstract:      {a['abstract']:.3f}")
        print(f"  Philosophical: {a['philosophical']:.3f}")
        print(f"  Trend: {a['trend']}, Range: {a['range']:.3f}")

    # ==========================================================================
    # Language Effects
    # ==========================================================================
    print("\n" + "-" * 80)
    print("CROSS-LINGUAL INVARIANCE")
    print("-" * 80)

    for l in analysis["language_effects"]:
        print(f"  By language: {l['by_language']}")
        print(f"  Variance across languages: {l['variance_across_languages']:.4f}")
        print(
            f"  Invariant: {'YES ✓' if l['invariant'] else 'NO - language affects judgment'}"
        )

    # ==========================================================================
    # Emotional Priming
    # ==========================================================================
    print("\n" + "-" * 80)
    print("EMOTIONAL PRIMING EFFECTS")
    print("-" * 80)

    for e in analysis["emotional_effects"]:
        direction = "↑" if e["shift"] > 0 else "↓"
        print(
            f"  {e['emotion']}: {e['neutral_mean']:.3f} → {e['primed_mean']:.3f} "
            f"({direction} {abs(e['shift']):.3f})"
        )

    # ==========================================================================
    # Anomalies
    # ==========================================================================
    if analysis["anomalies"]:
        print("\n" + "-" * 80)
        print("ANOMALIES DETECTED")
        print("-" * 80)
        for a in analysis["anomalies"]:
            print(f"  {a['type']}: {a.get('axis', 'N/A')} (z={a['z_score']:.2f})")

    # ==========================================================================
    # By Axis Summary
    # ==========================================================================
    print("\n" + "-" * 80)
    print("BY AXIS SUMMARY")
    print("-" * 80)

    axis_stats = analysis["by_dimension"]["axis"]
    for axis, stats in sorted(
        axis_stats.items(), key=lambda x: -(x[1].get("mean") or 0)
    ):
        if stats["mean"] is not None:
            print(
                f"  {axis:<12}: mean={stats['mean']:.3f}, std={stats['std']:.3f}, n={stats['n']}"
            )

    # Save full analysis
    path = output_dir / "qnd_fuzz_analysis.json"
    with open(path, "w") as f:
        json.dump(analysis, f, indent=2, default=str)

    print(f"\nFull analysis saved to: {path}")


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(description="QND Fuzzer - Structure Discovery")

    parser.add_argument("--api-key", required=True)
    parser.add_argument(
        "--mode", choices=["submit", "status", "results"], required=True
    )
    parser.add_argument("--batch-id", help="Batch ID for status/results")

    parser.add_argument(
        "--n-samples", type=int, default=500, help="Number of random samples"
    )
    parser.add_argument(
        "--structured", action="store_true", help="Use structured fuzzing"
    )
    parser.add_argument(
        "--n-per-config", type=int, default=10, help="Samples per structured config"
    )

    parser.add_argument("--output-dir", default="qnd_fuzz_results")
    parser.add_argument("--model", default="claude-sonnet-4-20250514")
    parser.add_argument(
        "--seed", type=int, default=None, help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    client = anthropic.Anthropic(api_key=args.api_key)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # ==========================================================================
    # SUBMIT
    # ==========================================================================
    if args.mode == "submit":

        if args.structured:
            print("Generating structured fuzz samples...")
            samples = generate_structured_fuzz(args.n_per_config)
        else:
            print(f"Generating {args.n_samples} random fuzz samples...")
            samples = generate_fuzz_samples(args.n_samples, args.seed)

        print(f"Generated {len(samples)} samples")

        # Build requests
        requests = []
        for sample in samples:
            requests.append(
                {
                    "custom_id": sample.sample_id,
                    "params": {
                        "model": args.model,
                        "max_tokens": 150,
                        "messages": [{"role": "user", "content": sample.prompt}],
                    },
                }
            )

        # Cost estimate
        cost = len(requests) * (500 * 1.5 + 80 * 7.5) / 1e6

        print(f"Total requests: {len(requests)}")
        print(f"Estimated cost: ${cost:.2f}")

        # Pre-registration
        prereg = hashlib.sha256(
            json.dumps(
                {
                    "n_samples": len(samples),
                    "structured": args.structured,
                    "seed": args.seed,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()[:16]

        print(f"Pre-registration hash: {prereg}")

        # Save samples
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        samples_path = output_dir / f"fuzz_samples_{ts}.json"
        with open(samples_path, "w") as f:
            json.dump(
                {"prereg": prereg, "samples": [s.to_dict() for s in samples]},
                f,
                indent=2,
            )

        # Submit
        batch = client.messages.batches.create(requests=requests)

        print(f"\nBatch submitted: {batch.id}")
        print(f"Status: {batch.processing_status}")

        # Save batch info
        with open(output_dir / f"fuzz_batch_{ts}.json", "w") as f:
            json.dump(
                {"batch_id": batch.id, "prereg": prereg, "n_samples": len(samples)}, f
            )

    # ==========================================================================
    # STATUS
    # ==========================================================================
    elif args.mode == "status":
        if not args.batch_id:
            print("Error: --batch-id required")
            return

        batch = client.messages.batches.retrieve(args.batch_id)
        print(f"Batch: {args.batch_id}")
        print(f"Status: {batch.processing_status}")
        print(f"Counts: {batch.request_counts}")

    # ==========================================================================
    # RESULTS
    # ==========================================================================
    elif args.mode == "results":
        if not args.batch_id:
            print("Error: --batch-id required")
            return

        # Load samples
        samples_files = sorted(output_dir.glob("fuzz_samples_*.json"))
        if not samples_files:
            print("Error: No samples file found")
            return

        with open(samples_files[-1]) as f:
            data = json.load(f)

        # Reconstruct samples
        samples = []
        for s_dict in data["samples"]:
            s = FuzzSample(**{k: v for k, v in s_dict.items() if k != "prompt"})
            s.prompt = s_dict.get("prompt", "")
            samples.append(s)

        print(f"Loaded {len(samples)} sample specs")
        print(f"Retrieving results for {args.batch_id}...")

        # Retrieve results
        results = {}
        for r in client.messages.batches.results(args.batch_id):
            sample = next((s for s in samples if s.sample_id == r.custom_id), None)
            response_type = sample.response_type if sample else "binary"

            if r.result.type == "succeeded":
                text = r.result.message.content[0].text
                parsed = parse_response(text, response_type)
                results[r.custom_id] = parsed
            else:
                results[r.custom_id] = {"parsed": False, "error": r.result.type}

        print(f"Retrieved {len(results)} results")

        # Analyze
        analysis = analyze_fuzz_results(results, samples)

        # Print
        print_fuzz_analysis(analysis, output_dir)


if __name__ == "__main__":
    main()
