#!/usr/bin/env python3
"""
QND Interference Probe v1.0

Targeted test of the timing interference effect discovered in fuzzing.

Finding: "During" measurement showed 47% deviation from classical expectation.
This script does high-n replication across multiple scenarios and axes.

Classical prediction: P(during) = [P(before) + P(after)] / 2
Quantum prediction: P(during) can exceed or fall below classical due to interference

Usage:
    python qnd_interference_v1.py --api-key KEY --mode submit --n-trials 200
"""

import argparse
import json
import math
import secrets
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict
import sys

try:
    import anthropic
except ImportError:
    print("pip install anthropic")
    sys.exit(1)


# =============================================================================
# SCENARIOS - Multiple to ensure effect isn't scenario-specific
# =============================================================================

SCENARIOS = {
    "trolley": {
        "before": """A runaway trolley is heading toward 5 people. Person A is standing next to a lever.

If A pulls the lever, the trolley will divert to a side track, killing 1 person instead of 5.

Person A is about to decide whether to pull the lever. A has not yet acted.""",
        "during": """A runaway trolley is heading toward 5 people. Person A is standing next to a lever.

If A pulls the lever, the trolley will divert to a side track, killing 1 person instead of 5.

Right now, in this moment, Person A is deciding whether to pull the lever. The decision is happening.""",
        "after": """A runaway trolley was heading toward 5 people. Person A was standing next to a lever.

If A pulled the lever, the trolley would divert to a side track, killing 1 person instead of 5.

Person A pulled the lever. The trolley diverted. 1 person died. 5 were saved.""",
    },
    "drowning": {
        "before": """Person A is walking past a pond where a child is drowning. A can easily save the child but would ruin their expensive clothes.

Person A is about to decide whether to save the child. A has not yet acted.""",
        "during": """Person A is walking past a pond where a child is drowning. A can easily save the child but would ruin their expensive clothes.

Right now, in this moment, Person A is deciding whether to save the child. The decision is happening.""",
        "after": """Person A was walking past a pond where a child was drowning. A could have easily saved the child but would have ruined their expensive clothes.

Person A did not save the child. The child drowned. A's clothes remained pristine.""",
    },
    "promise": {
        "before": """Person A promised to help their friend move apartments today. A just received an invitation to an exciting party happening at the same time.

Person A is about to decide whether to keep the promise or go to the party. A has not yet acted.""",
        "during": """Person A promised to help their friend move apartments today. A just received an invitation to an exciting party happening at the same time.

Right now, in this moment, Person A is deciding whether to keep the promise or go to the party. The decision is happening.""",
        "after": """Person A had promised to help their friend move apartments. A received an invitation to an exciting party at the same time.

Person A went to the party. The friend had to move alone.""",
    },
    "whistle": {
        "before": """Person A works at a company that is secretly dumping toxic waste. Reporting it would save lives but A would lose their job and face retaliation.

Person A is about to decide whether to blow the whistle. A has not yet acted.""",
        "during": """Person A works at a company that is secretly dumping toxic waste. Reporting it would save lives but A would lose their job and face retaliation.

Right now, in this moment, Person A is deciding whether to blow the whistle. The decision is happening.""",
        "after": """Person A worked at a company that was secretly dumping toxic waste. Reporting it would have saved lives but A would have lost their job and faced retaliation.

Person A did not blow the whistle. The dumping continued. A kept their job.""",
    },
    "lie": {
        "before": """A murderer asks Person A where their friend is hiding. A knows the friend's location. Telling the truth would lead to the friend's death.

Person A is about to decide whether to lie to the murderer. A has not yet spoken.""",
        "during": """A murderer asks Person A where their friend is hiding. A knows the friend's location. Telling the truth would lead to the friend's death.

Right now, in this moment, Person A is deciding whether to lie. The words are forming.""",
        "after": """A murderer asked Person A where their friend was hiding. A knew the friend's location. Telling the truth would have led to the friend's death.

Person A told the truth. The murderer found and killed the friend.""",
    },
}

# Axes that showed variation (not the 0.000 ones)
AXES = [
    ("harm", "Did Person A cause harm or allow harm to occur?"),
    ("intent", "Did Person A intend a bad outcome?"),
    ("duty", "Did Person A violate a moral duty?"),
    ("rights", "Did Person A violate someone's rights?"),
    ("fairness", "Did Person A act unfairly?"),
    ("virtue", "Did Person A's action reflect poor character?"),
    ("consent", "Did Person A act without proper consent?"),
    ("liberty", "Did Person A wrongly restrict someone's freedom?"),
]

PROMPT_TEMPLATE = """Evaluate this scenario:

{scenario}

Question ({axis_name}): {axis_question}

Answer YES if Person A acted wrongly according to this criterion.
Answer NO if Person A acted permissibly according to this criterion.

Respond with ONLY JSON:
{{"answer": "YES" or "NO", "probability": 0.0-1.0, "reasoning": "one sentence"}}"""


def generate_requests(n_trials: int, model: str):
    """Generate all requests for interference test."""

    requests = []
    specs = []

    timings = ["before", "during", "after"]

    for scenario_name, scenario_texts in SCENARIOS.items():
        for axis_name, axis_question in AXES:
            for timing in timings:
                for trial in range(n_trials):

                    prompt = PROMPT_TEMPLATE.format(
                        scenario=scenario_texts[timing],
                        axis_name=axis_name,
                        axis_question=axis_question,
                    )

                    salt = secrets.token_hex(4)
                    custom_id = f"interf_{scenario_name[:4]}_{axis_name[:4]}_{timing[:3]}_{trial:03d}_{salt}"

                    requests.append(
                        {
                            "custom_id": custom_id,
                            "params": {
                                "model": model,
                                "max_tokens": 150,
                                "messages": [{"role": "user", "content": prompt}],
                            },
                        }
                    )

                    specs.append(
                        {
                            "custom_id": custom_id,
                            "scenario": scenario_name,
                            "axis": axis_name,
                            "timing": timing,
                            "trial": trial,
                        }
                    )

    return requests, specs


def parse_response(text: str) -> Dict:
    """Parse response."""
    import re

    result = {"parsed": False, "answer": None, "probability": None}

    try:
        clean = text.strip()
        if "```" in clean:
            clean = clean.split("```")[1].replace("json", "").strip()

        data = json.loads(clean)

        ans = data.get("answer", "").upper()
        if "YES" in ans:
            result["answer"] = 1
            result["parsed"] = True
        elif "NO" in ans:
            result["answer"] = 0
            result["parsed"] = True

        prob = data.get("probability")
        if prob is not None:
            result["probability"] = float(prob)

    except:
        if "YES" in text.upper():
            result["answer"] = 1
            result["parsed"] = True
        elif "NO" in text.upper():
            result["answer"] = 0
            result["parsed"] = True

    return result


def analyze_interference(results: Dict, specs: List[Dict]) -> Dict:
    """Analyze for interference effects."""

    spec_map = {s["custom_id"]: s for s in specs}

    # Group by scenario × axis
    groups = defaultdict(lambda: {"before": [], "during": [], "after": []})

    parsed = 0
    for cid, res in results.items():
        if not res.get("parsed"):
            continue
        parsed += 1

        spec = spec_map.get(cid, {})
        key = (spec.get("scenario"), spec.get("axis"))
        timing = spec.get("timing")

        # Use answer (0/1) as the value
        val = res.get("answer")
        if val is not None:
            groups[key][timing].append(val)

    # Compute interference for each group
    analysis = {
        "summary": {"total": len(results), "parsed": parsed},
        "by_group": [],
        "aggregate": {"before": [], "during": [], "after": []},
        "interference_detected": False,
    }

    for (scenario, axis), timings in groups.items():
        before = timings["before"]
        during = timings["during"]
        after = timings["after"]

        if not (before and during and after):
            continue

        # Means
        m_before = sum(before) / len(before)
        m_during = sum(during) / len(during)
        m_after = sum(after) / len(after)

        # Classical expectation
        classical = (m_before + m_after) / 2

        # Interference
        interference = m_during - classical
        interference_pct = (interference / classical * 100) if classical != 0 else 0

        # Standard errors for significance test
        def se(vals):
            if len(vals) < 2:
                return 1
            m = sum(vals) / len(vals)
            var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
            return math.sqrt(var / len(vals))

        se_during = se(during)
        se_classical = math.sqrt(se(before) ** 2 + se(after) ** 2) / 2
        se_diff = math.sqrt(se_during**2 + se_classical**2)

        t_stat = abs(interference) / se_diff if se_diff > 0 else 0
        significant = t_stat > 2.0

        group_result = {
            "scenario": scenario,
            "axis": axis,
            "n_before": len(before),
            "n_during": len(during),
            "n_after": len(after),
            "mean_before": m_before,
            "mean_during": m_during,
            "mean_after": m_after,
            "classical_expectation": classical,
            "interference": interference,
            "interference_pct": interference_pct,
            "t_statistic": t_stat,
            "significant": significant,
        }

        analysis["by_group"].append(group_result)

        # Aggregate
        analysis["aggregate"]["before"].extend(before)
        analysis["aggregate"]["during"].extend(during)
        analysis["aggregate"]["after"].extend(after)

        if significant and abs(interference_pct) > 10:
            analysis["interference_detected"] = True

    # Aggregate statistics
    agg = analysis["aggregate"]
    if agg["before"] and agg["during"] and agg["after"]:
        m_b = sum(agg["before"]) / len(agg["before"])
        m_d = sum(agg["during"]) / len(agg["during"])
        m_a = sum(agg["after"]) / len(agg["after"])
        classical = (m_b + m_a) / 2
        interference = m_d - classical

        analysis["aggregate_stats"] = {
            "mean_before": m_b,
            "mean_during": m_d,
            "mean_after": m_a,
            "classical_expectation": classical,
            "interference": interference,
            "interference_pct": (
                (interference / classical * 100) if classical != 0 else 0
            ),
        }

    return analysis


def print_analysis(analysis: Dict, output_dir: Path):
    """Print interference analysis."""

    print("\n" + "=" * 80)
    print("QND INTERFERENCE PROBE - RESULTS")
    print("=" * 80)
    print("Testing: P(during) vs [P(before) + P(after)] / 2")
    print("Classical: during = average of before/after")
    print("Quantum: during can show interference (deviation from average)")
    print("=" * 80)

    s = analysis["summary"]
    print(f"\nParsed: {s['parsed']}/{s['total']}")

    # Aggregate
    if "aggregate_stats" in analysis:
        a = analysis["aggregate_stats"]
        print("\n" + "-" * 80)
        print("AGGREGATE (all scenarios, all axes)")
        print("-" * 80)
        print(f"  P(before):  {a['mean_before']:.4f}")
        print(f"  P(during):  {a['mean_during']:.4f}")
        print(f"  P(after):   {a['mean_after']:.4f}")
        print(f"  Classical:  {a['classical_expectation']:.4f}")
        print(
            f"  Interference: {a['interference']:+.4f} ({a['interference_pct']:+.1f}%)"
        )

        if abs(a["interference_pct"]) > 20:
            print("\n  ★★★ STRONG INTERFERENCE DETECTED ★★★")
        elif abs(a["interference_pct"]) > 10:
            print("\n  ★★ MODERATE INTERFERENCE DETECTED ★★")
        elif abs(a["interference_pct"]) > 5:
            print("\n  ★ WEAK INTERFERENCE DETECTED ★")
        else:
            print("\n  No significant interference (classical behavior)")

    # By group
    print("\n" + "-" * 80)
    print("BY SCENARIO × AXIS")
    print("-" * 80)

    # Sort by interference magnitude
    groups = sorted(analysis["by_group"], key=lambda x: -abs(x["interference_pct"]))

    significant_count = 0
    for g in groups:
        sig = "★" if g["significant"] else " "
        print(
            f"{sig} {g['scenario'][:8]:<8} × {g['axis'][:8]:<8}: "
            f"B={g['mean_before']:.2f} D={g['mean_during']:.2f} A={g['mean_after']:.2f} "
            f"→ interf={g['interference_pct']:+.1f}% (t={g['t_statistic']:.1f})"
        )
        if g["significant"]:
            significant_count += 1

    print(f"\nSignificant effects: {significant_count}/{len(groups)}")

    # Interpretation
    print("\n" + "=" * 80)
    print("INTERPRETATION")
    print("=" * 80)

    if analysis.get("interference_detected"):
        print(
            """
INTERFERENCE CONFIRMED

The probability of judging an action as wrong DURING the decision
differs systematically from the classical expectation (average of 
before/after).

This is consistent with quantum-like superposition: the moral state
during decision is not a classical mixture of before/after states,
but a superposition with interference terms.

Constructive interference (during > classical): amplitudes adding
Destructive interference (during < classical): amplitudes canceling
"""
        )
    else:
        print(
            """
NO SIGNIFICANT INTERFERENCE

The probability during decision matches the classical expectation.
This is consistent with classical probability: the state during
decision is a mixture, not a superposition.
"""
        )

    # Save
    path = output_dir / "qnd_interference_results.json"
    with open(path, "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"\nResults saved to: {path}")


def main():
    parser = argparse.ArgumentParser(description="QND Interference Probe")
    parser.add_argument("--api-key", required=True)
    parser.add_argument(
        "--mode", choices=["submit", "status", "results"], required=True
    )
    parser.add_argument("--batch-id")
    parser.add_argument("--n-trials", type=int, default=100)
    parser.add_argument("--output-dir", default="qnd_interference_results")
    parser.add_argument("--model", default="claude-sonnet-4-20250514")

    args = parser.parse_args()

    client = anthropic.Anthropic(api_key=args.api_key)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    if args.mode == "submit":
        requests, specs = generate_requests(args.n_trials, args.model)

        # Info
        n_scenarios = len(SCENARIOS)
        n_axes = len(AXES)
        n_timings = 3
        total = n_scenarios * n_axes * n_timings * args.n_trials

        print(f"Scenarios: {n_scenarios}")
        print(f"Axes: {n_axes}")
        print(f"Timings: {n_timings}")
        print(f"Trials per config: {args.n_trials}")
        print(f"Total requests: {total}")

        cost = total * (500 * 1.5 + 100 * 7.5) / 1e6
        print(f"Estimated cost: ${cost:.2f}")

        # Save specs
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        prereg = hashlib.sha256(json.dumps({"n": total}).encode()).hexdigest()[:16]

        with open(output_dir / f"specs_{ts}.json", "w") as f:
            json.dump({"prereg": prereg, "specs": specs}, f)

        # Submit
        batch = client.messages.batches.create(requests=requests)
        print(f"\nBatch: {batch.id}")
        print(f"Status: {batch.processing_status}")

        with open(output_dir / f"batch_{ts}.json", "w") as f:
            json.dump({"batch_id": batch.id, "prereg": prereg}, f)

    elif args.mode == "status":
        batch = client.messages.batches.retrieve(args.batch_id)
        print(f"Status: {batch.processing_status}")
        print(f"Counts: {batch.request_counts}")

    elif args.mode == "results":
        # Load specs
        specs_files = sorted(output_dir.glob("specs_*.json"))
        with open(specs_files[-1]) as f:
            data = json.load(f)
        specs = data["specs"]

        print(f"Retrieving {args.batch_id}...")

        results = {}
        for r in client.messages.batches.results(args.batch_id):
            if r.result.type == "succeeded":
                text = r.result.message.content[0].text
                results[r.custom_id] = parse_response(text)
            else:
                results[r.custom_id] = {"parsed": False}

        print(f"Retrieved {len(results)} results")

        analysis = analyze_interference(results, specs)
        print_analysis(analysis, output_dir)


if __name__ == "__main__":
    main()
