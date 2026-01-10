#!/usr/bin/env python3
"""
QND Commutator Matrix v1.0

Map the full non-commutativity structure of moral judgment.

We know order effects exist (6.3σ original, 10 significant pairs in fuzzing).
Now we systematically measure [A,B] for all axis pairs to build the full
commutator matrix.

For each pair of axes (A,B):
- Measure A first, then B → get P(guilty|A→B)  
- Measure B first, then A → get P(guilty|B→A)
- Commutator strength: |P(A→B) - P(B→A)|

Output: 12×12 matrix showing which moral frameworks interfere with each other.

Usage:
    python qnd_commutator_v1.py --api-key KEY --mode submit --n-trials 50
    python qnd_commutator_v1.py --api-key KEY --mode results --batch-id BATCH_ID
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
# MORAL AXES - The observables we're measuring
# =============================================================================

# 8 axes that showed variation in fuzzing (excluding care, authority, sanctity, loyalty which were 0)
AXES = [
    ("harm", "Did this action cause harm?"),
    ("intent", "Was there intent to cause a bad outcome?"),
    ("duty", "Was a moral duty violated?"),
    ("rights", "Were someone's rights violated?"),
    ("fairness", "Was this action unfair?"),
    ("virtue", "Does this action reflect poor moral character?"),
    ("consent", "Was this action taken without proper consent?"),
    ("liberty", "Did this action wrongly restrict someone's freedom?"),
]

AXIS_NAMES = [a[0] for a in AXES]
AXIS_MAP = {a[0]: a[1] for a in AXES}


# =============================================================================
# SCENARIOS - Morally ambiguous cases where order might matter
# =============================================================================

SCENARIOS = [
    {
        "id": "trolley",
        "text": """A runaway trolley will kill 5 people. Person A pulls a lever to divert it to a side track, where it kills 1 person instead. The 5 are saved, but 1 dies due to A's action.""",
        "subject": "Person A",
    },
    {
        "id": "whistleblower",
        "text": """Person A works at a company illegally dumping toxic waste. A leaks documents to the press, exposing the crime. The company faces penalties, A loses their job, and several executives go to prison.""",
        "subject": "Person A",
    },
    {
        "id": "lie_to_murderer",
        "text": """A murderer asks Person A where their friend is hiding. A lies, saying the friend went north when they actually went south. The murderer goes north. The friend survives.""",
        "subject": "Person A",
    },
    {
        "id": "broken_promise",
        "text": """Person A promised to help their friend move today. A's child gets sick. A breaks the promise to care for the sick child. The friend has to hire movers at significant expense.""",
        "subject": "Person A",
    },
    {
        "id": "expensive_rescue",
        "text": """Person A walks past a drowning child. A could easily save the child but would ruin a $500 suit. A saves the child, ruining the suit.""",
        "subject": "Person A",
    },
    {
        "id": "triage",
        "text": """Doctor A has one dose of medicine. Patient X (elderly, 10% survival chance) arrived first. Patient Y (young, 90% survival chance) arrived second. A gives the medicine to Patient Y. Patient X dies.""",
        "subject": "Doctor A",
    },
]


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

# Two-question prompt: asks both axes in sequence, order varies
PROMPT_TEMPLATE = """Consider this scenario:

{scenario}

You must evaluate {subject}'s action by answering two questions in the order given.

FIRST QUESTION ({axis1_name}): {axis1_question}
Think about this carefully, then answer YES or NO.

SECOND QUESTION ({axis2_name}): {axis2_question}
Think about this carefully, then answer YES or NO.

Respond with ONLY this JSON format:
{{"first_answer": "YES" or "NO", "first_reasoning": "one sentence", "second_answer": "YES" or "NO", "second_reasoning": "one sentence"}}"""


def generate_requests(n_trials: int, model: str) -> Tuple[List[Dict], List[Dict]]:
    """Generate requests for all axis pairs in both orders."""

    requests = []
    specs = []

    n_axes = len(AXES)

    for scenario in SCENARIOS:
        # All pairs (including both orderings)
        for i in range(n_axes):
            for j in range(n_axes):
                if i == j:
                    continue  # Skip same-axis pairs

                axis1_name, axis1_q = AXES[i]
                axis2_name, axis2_q = AXES[j]

                for trial in range(n_trials):
                    prompt = PROMPT_TEMPLATE.format(
                        scenario=scenario["text"],
                        subject=scenario["subject"],
                        axis1_name=axis1_name,
                        axis1_question=axis1_q,
                        axis2_name=axis2_name,
                        axis2_question=axis2_q,
                    )

                    salt = secrets.token_hex(4)
                    custom_id = f"comm_{scenario['id'][:4]}_{axis1_name[:3]}_{axis2_name[:3]}_{trial:03d}_{salt}"

                    requests.append(
                        {
                            "custom_id": custom_id,
                            "params": {
                                "model": model,
                                "max_tokens": 200,
                                "messages": [{"role": "user", "content": prompt}],
                            },
                        }
                    )

                    specs.append(
                        {
                            "custom_id": custom_id,
                            "scenario": scenario["id"],
                            "axis1": axis1_name,
                            "axis2": axis2_name,
                            "trial": trial,
                            "order": f"{axis1_name}→{axis2_name}",
                        }
                    )

    return requests, specs


def parse_response(text: str) -> Dict:
    """Parse the two-answer response."""
    import re

    result = {"parsed": False, "first": None, "second": None}

    try:
        clean = text.strip()
        if "```" in clean:
            clean = clean.split("```")[1].replace("json", "").strip()

        data = json.loads(clean)

        first = data.get("first_answer", "").upper()
        second = data.get("second_answer", "").upper()

        if "YES" in first:
            result["first"] = 1
        elif "NO" in first:
            result["first"] = 0

        if "YES" in second:
            result["second"] = 1
        elif "NO" in second:
            result["second"] = 0

        if result["first"] is not None and result["second"] is not None:
            result["parsed"] = True

    except:
        # Regex fallback
        first_match = re.search(r'"first_answer"\s*:\s*"(YES|NO)"', text, re.I)
        second_match = re.search(r'"second_answer"\s*:\s*"(YES|NO)"', text, re.I)

        if first_match:
            result["first"] = 1 if first_match.group(1).upper() == "YES" else 0
        if second_match:
            result["second"] = 1 if second_match.group(1).upper() == "YES" else 0

        if result["first"] is not None and result["second"] is not None:
            result["parsed"] = True

    return result


def analyze_commutators(results: Dict, specs: List[Dict]) -> Dict:
    """Build the commutator matrix."""

    spec_map = {s["custom_id"]: s for s in specs}

    # Group by (axis1, axis2) - note: we measure SECOND axis response
    # When order is A→B, we're interested in P(B|A measured first)
    # When order is B→A, we're interested in P(A|B measured first)

    # For commutator [A,B], we compare:
    # - Response to B when A was asked first
    # - Response to B when B was asked first (i.e., A asked second)

    # Structure: effects[axis_measured][axis_context] = list of responses
    # axis_context = what was asked FIRST
    effects = defaultdict(lambda: defaultdict(list))

    parsed = 0
    for cid, res in results.items():
        if not res.get("parsed"):
            continue
        parsed += 1

        spec = spec_map.get(cid, {})
        axis1 = spec.get("axis1")  # Asked first
        axis2 = spec.get("axis2")  # Asked second

        # Record: response to axis2 in context where axis1 was first
        effects[axis2][axis1].append(res["second"])

        # Also record: response to axis1 when it's first (context = "none" or self)
        effects[axis1]["_first"].append(res["first"])

    # Build commutator matrix
    # [A,B] = P(A | B first) - P(A | A first)
    # This measures how much measuring B first changes the response to A

    n_axes = len(AXIS_NAMES)
    matrix = {}
    significant = []

    for target in AXIS_NAMES:
        matrix[target] = {}

        # Baseline: P(target | target asked first)
        baseline_responses = effects[target]["_first"]
        if not baseline_responses:
            continue
        baseline = sum(baseline_responses) / len(baseline_responses)
        baseline_n = len(baseline_responses)
        baseline_se = (
            math.sqrt(baseline * (1 - baseline) / baseline_n) if baseline_n > 1 else 1
        )

        for context in AXIS_NAMES:
            if context == target:
                matrix[target][context] = {"commutator": 0, "significant": False}
                continue

            # P(target | context asked first)
            context_responses = effects[target][context]
            if not context_responses:
                matrix[target][context] = {"commutator": None, "significant": False}
                continue

            context_mean = sum(context_responses) / len(context_responses)
            context_n = len(context_responses)
            context_se = (
                math.sqrt(context_mean * (1 - context_mean) / context_n)
                if context_n > 1
                else 1
            )

            # Commutator: difference
            comm = context_mean - baseline
            se_diff = math.sqrt(baseline_se**2 + context_se**2)
            t_stat = abs(comm) / se_diff if se_diff > 0 else 0
            sig = t_stat > 2.0

            matrix[target][context] = {
                "baseline": baseline,
                "with_context": context_mean,
                "commutator": comm,
                "se": se_diff,
                "t": t_stat,
                "significant": sig,
                "n_baseline": baseline_n,
                "n_context": context_n,
            }

            if sig:
                significant.append(
                    {
                        "target": target,
                        "context": context,
                        "commutator": comm,
                        "t": t_stat,
                        "baseline": baseline,
                        "with_context": context_mean,
                    }
                )

    # Sort significant effects
    significant.sort(key=lambda x: -abs(x["commutator"]))

    return {
        "summary": {"total": len(results), "parsed": parsed},
        "matrix": matrix,
        "significant": significant,
        "n_significant": len(significant),
    }


def print_analysis(analysis: Dict, output_dir: Path):
    """Print commutator analysis."""

    print("\n" + "=" * 80)
    print("QND COMMUTATOR MATRIX - NON-COMMUTATIVITY STRUCTURE")
    print("=" * 80)
    print("[A,B] = P(A | B first) - P(A | A first)")
    print("Measures: How much does measuring B first change response to A?")
    print("=" * 80)

    s = analysis["summary"]
    print(f"\nParsed: {s['parsed']}/{s['total']}")

    # Significant effects
    print("\n" + "-" * 80)
    print(f"SIGNIFICANT NON-COMMUTING PAIRS ({analysis['n_significant']} found)")
    print("-" * 80)

    if analysis["significant"]:
        print(
            f"{'Target':<12} {'Context':<12} {'[C,T]':>8} {'t-stat':>8} {'P(T|T)':>8} {'P(T|C)':>8}"
        )
        print("-" * 64)

        for eff in analysis["significant"][:20]:  # Top 20
            print(
                f"{eff['target']:<12} {eff['context']:<12} "
                f"{eff['commutator']:>+8.3f} {eff['t']:>8.2f} "
                f"{eff['baseline']:>8.3f} {eff['with_context']:>8.3f}"
            )
    else:
        print("No significant non-commuting pairs found.")

    # Matrix visualization (simplified)
    print("\n" + "-" * 80)
    print("COMMUTATOR MATRIX SUMMARY")
    print("-" * 80)
    print("(Showing only pairs with |[A,B]| > 0.1)")
    print()

    matrix = analysis["matrix"]
    strong_pairs = []

    for target, contexts in matrix.items():
        for context, data in contexts.items():
            if data.get("commutator") and abs(data["commutator"]) > 0.1:
                strong_pairs.append(
                    (
                        target,
                        context,
                        data["commutator"],
                        data.get("significant", False),
                    )
                )

    strong_pairs.sort(key=lambda x: -abs(x[2]))

    for target, context, comm, sig in strong_pairs[:30]:
        marker = "★" if sig else " "
        print(f"{marker} [{context:<10}, {target:<10}] = {comm:+.3f}")

    # Axis summary: which axes are most affected by context?
    print("\n" + "-" * 80)
    print("AXIS SENSITIVITY (how much is each axis affected by prior questions?)")
    print("-" * 80)

    axis_sensitivity = {}
    for target, contexts in matrix.items():
        effects = [
            abs(d["commutator"])
            for d in contexts.values()
            if d.get("commutator") is not None and d["commutator"] != 0
        ]
        if effects:
            axis_sensitivity[target] = sum(effects) / len(effects)

    for axis, sensitivity in sorted(axis_sensitivity.items(), key=lambda x: -x[1]):
        bar = "█" * int(sensitivity * 50)
        print(f"  {axis:<12}: {sensitivity:.3f} {bar}")

    # Context power: which axes most affect others?
    print("\n" + "-" * 80)
    print("CONTEXT POWER (how much does asking this axis first affect others?)")
    print("-" * 80)

    context_power = defaultdict(list)
    for target, contexts in matrix.items():
        for context, data in contexts.items():
            if data.get("commutator") is not None and context != target:
                context_power[context].append(abs(data["commutator"]))

    context_avg = {k: sum(v) / len(v) for k, v in context_power.items() if v}

    for axis, power in sorted(context_avg.items(), key=lambda x: -x[1]):
        bar = "█" * int(power * 50)
        print(f"  {axis:<12}: {power:.3f} {bar}")

    # Interpretation
    print("\n" + "=" * 80)
    print("INTERPRETATION")
    print("=" * 80)

    n_sig = analysis["n_significant"]
    total_pairs = len(AXIS_NAMES) * (len(AXIS_NAMES) - 1)

    print(
        f"""
Non-commuting pairs: {n_sig}/{total_pairs} ({100*n_sig/total_pairs:.1f}%)

This means: For {n_sig} pairs of moral frameworks, the order in which
you consider them changes your judgment. Measuring framework A first
shifts your subsequent assessment under framework B.

In quantum terms: These frameworks are incompatible observables.
[A,B] ≠ 0 means A and B cannot be simultaneously definite.
"""
    )

    if n_sig > total_pairs * 0.1:
        print("★ SUBSTANTIAL NON-COMMUTATIVITY DETECTED")
        print("  Moral judgment shows widespread order effects.")

    # Save
    path = output_dir / "qnd_commutator_results.json"
    with open(path, "w") as f:
        json.dump(analysis, f, indent=2, default=str)
    print(f"\nResults saved to: {path}")


def main():
    parser = argparse.ArgumentParser(description="QND Commutator Matrix")
    parser.add_argument("--api-key", required=True)
    parser.add_argument(
        "--mode", choices=["submit", "status", "results"], required=True
    )
    parser.add_argument("--batch-id")
    parser.add_argument("--n-trials", type=int, default=50)
    parser.add_argument("--output-dir", default="qnd_commutator_results")
    parser.add_argument("--model", default="claude-sonnet-4-20250514")

    args = parser.parse_args()

    client = anthropic.Anthropic(api_key=args.api_key)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    if args.mode == "submit":
        requests, specs = generate_requests(args.n_trials, args.model)

        n_scenarios = len(SCENARIOS)
        n_axes = len(AXES)
        n_pairs = n_axes * (n_axes - 1)  # Ordered pairs
        total = n_scenarios * n_pairs * args.n_trials

        print(f"Scenarios: {n_scenarios}")
        print(f"Axes: {n_axes}")
        print(f"Ordered pairs: {n_pairs}")
        print(f"Trials per config: {args.n_trials}")
        print(f"Total requests: {total}")

        cost = total * (600 * 1.5 + 150 * 7.5) / 1e6
        print(f"Estimated cost: ${cost:.2f}")

        # Save
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        prereg = hashlib.sha256(json.dumps({"n": total}).encode()).hexdigest()[:16]

        with open(output_dir / f"specs_{ts}.json", "w") as f:
            json.dump({"prereg": prereg, "specs": specs}, f)

        batch = client.messages.batches.create(requests=requests)
        print(f"\nBatch: {batch.id}")

        with open(output_dir / f"batch_{ts}.json", "w") as f:
            json.dump({"batch_id": batch.id, "prereg": prereg}, f)

    elif args.mode == "status":
        batch = client.messages.batches.retrieve(args.batch_id)
        print(f"Status: {batch.processing_status}")
        print(f"Counts: {batch.request_counts}")

    elif args.mode == "results":
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

        print(f"Retrieved {len(results)}")

        analysis = analyze_commutators(results, specs)
        print_analysis(analysis, output_dir)


if __name__ == "__main__":
    main()
