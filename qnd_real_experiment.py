#!/usr/bin/env python3
"""
QND Experiment: Rigorous Order Effects Test in Moral Judgment

This script performs an ACTUAL test of order effects by making independent
API calls to Claude with different assessment orderings.

Usage:
    python qnd_real_experiment.py --data AITA_labeled_posts.csv --api-key sk-ant-... --n-posts 50

Requirements:
    pip install anthropic pandas scipy statsmodels

Author: QND Research
Date: December 2024
"""

import argparse
import json
import time
import random
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional
import pandas as pd
import anthropic
from scipy import stats
from scipy.stats import binomtest, fisher_exact
from statsmodels.stats.proportion import proportion_confint


# =============================================================================
# PROMPTS - The core of the experiment
# =============================================================================

SYSTEM_PROMPT = """You are an ethical judgment system. You will be given a scenario from Reddit's "Am I The Asshole" forum. 

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


PROMPT_ORDER_A = """Assess this scenario by following these steps IN ORDER:

STEP 1 - HARM ASSESSMENT: First, analyze the harm or negative consequences caused. Who was harmed? How severely? What damage occurred?

STEP 2 - INTENT ASSESSMENT: Second, analyze the intentions and motivations. What did the person intend? Were they acting in good faith or bad faith?

STEP 3 - VERDICT: Based on your harm-first, then intent analysis, provide your verdict.

SCENARIO:
Title: {title}

{content}

Remember: Assess HARM first, THEN Intent, THEN Verdict. Respond with JSON only."""


PROMPT_ORDER_B = """Assess this scenario by following these steps IN ORDER:

STEP 1 - INTENT ASSESSMENT: First, analyze the intentions and motivations. What did the person intend? Were they acting in good faith or bad faith?

STEP 2 - HARM ASSESSMENT: Second, analyze the harm or negative consequences caused. Who was harmed? How severely? What damage occurred?

STEP 3 - VERDICT: Based on your intent-first, then harm analysis, provide your verdict.

SCENARIO:
Title: {title}

{content}

Remember: Assess INTENT first, THEN Harm, THEN Verdict. Respond with JSON only."""


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
            
            # Extract text content
            text = response.content[0].text.strip()
            
            # Try to parse JSON
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


def run_single_test(
    client: anthropic.Anthropic,
    post: dict,
    delay_between_orders: float = 1.0,
    model: str = "claude-sonnet-4-20250514"
) -> dict:
    """Run both orderings on a single post and return results."""
    
    title = post.get("post_title", post.get("title", ""))
    content = post.get("post_content", post.get("content", ""))
    ground_truth = post.get("verdict", "UNKNOWN")
    post_id = post.get("post_id", hashlib.md5(content.encode()).hexdigest()[:8])
    
    # Randomize which order goes first to avoid any systematic bias
    orders = ["A", "B"]
    random.shuffle(orders)
    
    results = {"post_id": post_id, "ground_truth": ground_truth, "title": title[:60]}
    
    for order in orders:
        if order == "A":
            prompt = PROMPT_ORDER_A.format(title=title, content=content)
        else:
            prompt = PROMPT_ORDER_B.format(title=title, content=content)
        
        response = call_claude_api(client, prompt, model=model)
        
        if response:
            results[f"order_{order}_verdict"] = response.get("verdict", "ERROR")
            results[f"order_{order}_confidence"] = response.get("confidence", 0.0)
            results[f"order_{order}_raw"] = response
        else:
            results[f"order_{order}_verdict"] = "ERROR"
            results[f"order_{order}_confidence"] = 0.0
            results[f"order_{order}_raw"] = None
        
        # Delay between API calls
        time.sleep(delay_between_orders)
    
    # Determine if there's an order effect
    v_a = results.get("order_A_verdict", "ERROR")
    v_b = results.get("order_B_verdict", "ERROR")
    results["order_effect"] = (v_a != v_b) and (v_a != "ERROR") and (v_b != "ERROR")
    
    return results


# =============================================================================
# STATISTICAL ANALYSIS
# =============================================================================

def analyze_results(results: list[dict]) -> dict:
    """Perform statistical analysis on experiment results."""
    
    # Filter out errors
    valid_results = [r for r in results if r.get("order_A_verdict") != "ERROR" 
                     and r.get("order_B_verdict") != "ERROR"]
    
    n_total = len(valid_results)
    n_effects = sum(1 for r in valid_results if r.get("order_effect"))
    
    if n_total == 0:
        return {"error": "No valid results"}
    
    effect_rate = n_effects / n_total
    
    # Confidence interval
    ci_low, ci_high = proportion_confint(n_effects, n_total, alpha=0.05, method='wilson')
    
    # Binomial tests against various nulls
    tests = {}
    for null in [0.05, 0.10, 0.15, 0.20]:
        result = binomtest(n_effects, n_total, null, alternative='greater')
        z = (effect_rate - null) / (null * (1-null) / n_total) ** 0.5 if n_total > 0 else 0
        sigma = stats.norm.ppf(1 - result.pvalue) if result.pvalue > 1e-15 and result.pvalue < 0.5 else (8.0 if result.pvalue < 1e-15 else 0)
        tests[f"null_{int(null*100)}pct"] = {
            "p_value": result.pvalue,
            "z_score": z,
            "sigma": sigma
        }
    
    # Breakdown by ground truth verdict
    by_verdict = {}
    for r in valid_results:
        gt = r.get("ground_truth", "UNKNOWN")
        if gt not in by_verdict:
            by_verdict[gt] = {"total": 0, "effects": 0}
        by_verdict[gt]["total"] += 1
        if r.get("order_effect"):
            by_verdict[gt]["effects"] += 1
    
    # Calculate rates
    for v in by_verdict:
        by_verdict[v]["rate"] = by_verdict[v]["effects"] / by_verdict[v]["total"] if by_verdict[v]["total"] > 0 else 0
    
    # Clear (NTA) vs Contested
    nta_total = by_verdict.get("NTA", {}).get("total", 0)
    nta_effects = by_verdict.get("NTA", {}).get("effects", 0)
    contested_total = sum(by_verdict[v]["total"] for v in by_verdict if v != "NTA")
    contested_effects = sum(by_verdict[v]["effects"] for v in by_verdict if v != "NTA")
    
    nta_rate = nta_effects / nta_total if nta_total > 0 else 0
    contested_rate = contested_effects / contested_total if contested_total > 0 else 0
    
    # Fisher's exact test
    if nta_total > 0 and contested_total > 0:
        contingency = [
            [nta_effects, nta_total - nta_effects],
            [contested_effects, contested_total - contested_effects]
        ]
        odds_ratio, fisher_p = fisher_exact(contingency)
    else:
        odds_ratio, fisher_p = None, None
    
    # Transition analysis
    transitions = {}
    for r in valid_results:
        if r.get("order_effect"):
            v_a = r.get("order_A_verdict")
            v_b = r.get("order_B_verdict")
            trans = f"{v_a}→{v_b}"
            transitions[trans] = transitions.get(trans, 0) + 1
    
    return {
        "n_total": n_total,
        "n_effects": n_effects,
        "effect_rate": effect_rate,
        "ci_95": [ci_low, ci_high],
        "statistical_tests": tests,
        "by_verdict": by_verdict,
        "clear_vs_contested": {
            "nta_total": nta_total,
            "nta_effects": nta_effects,
            "nta_rate": nta_rate,
            "contested_total": contested_total,
            "contested_effects": contested_effects,
            "contested_rate": contested_rate,
            "odds_ratio": odds_ratio,
            "fisher_p": fisher_p,
            "relative_risk": contested_rate / nta_rate if nta_rate > 0 else None
        },
        "transitions": transitions
    }


def print_report(analysis: dict, results: list[dict]):
    """Print a formatted analysis report."""
    
    print("\n" + "=" * 70)
    print("QND EXPERIMENT: REAL API TEST RESULTS")
    print("=" * 70)
    
    print(f"\nSample Size: {analysis['n_total']} valid posts")
    print(f"Order Effects Detected: {analysis['n_effects']} ({analysis['effect_rate']:.1%})")
    print(f"95% CI: [{analysis['ci_95'][0]:.1%}, {analysis['ci_95'][1]:.1%}]")
    
    print("\n" + "-" * 70)
    print("Statistical Tests (one-tailed)")
    print("-" * 70)
    for null_name, test in analysis['statistical_tests'].items():
        null_pct = null_name.replace("null_", "").replace("pct", "%")
        print(f"  vs {null_pct:>4} null: p = {test['p_value']:.2e}, z = {test['z_score']:.2f}, ~{test['sigma']:.1f}σ")
    
    print("\n" + "-" * 70)
    print("By Ground Truth Verdict")
    print("-" * 70)
    for verdict, data in sorted(analysis['by_verdict'].items()):
        print(f"  {verdict}: {data['effects']}/{data['total']} = {data['rate']:.1%}")
    
    cvc = analysis['clear_vs_contested']
    print(f"\n  Clear (NTA):   {cvc['nta_effects']}/{cvc['nta_total']} = {cvc['nta_rate']:.1%}")
    print(f"  Contested:     {cvc['contested_effects']}/{cvc['contested_total']} = {cvc['contested_rate']:.1%}")
    if cvc['relative_risk']:
        print(f"  Relative Risk: {cvc['relative_risk']:.2f}x")
    if cvc['fisher_p']:
        print(f"  Fisher's p:    {cvc['fisher_p']:.4f}")
    
    print("\n" + "-" * 70)
    print("Transition Patterns (Order A → Order B)")
    print("-" * 70)
    for trans, count in sorted(analysis['transitions'].items(), key=lambda x: -x[1]):
        print(f"  {trans}: {count}")
    
    # Interpretation
    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    
    best_test = analysis['statistical_tests'].get('null_10pct', {})
    sigma = best_test.get('sigma', 0)
    
    if sigma >= 6:
        print("\n✓✓ 6-SIGMA ACHIEVED: Order effects are REAL with extreme confidence")
    elif sigma >= 5:
        print("\n✓ 5-SIGMA: Discovery-level significance achieved")
    elif sigma >= 3:
        print("\n✓ 3-SIGMA: Strong evidence for order effects")
    elif sigma >= 2:
        print("\n~ 2-SIGMA: Suggestive evidence, needs more data")
    else:
        print("\n✗ Insufficient evidence for order effects at this sample size")
    
    print(f"\nThe observed {analysis['effect_rate']:.1%} order effect rate suggests that")
    print("moral judgment {'DOES' if sigma >= 3 else 'may'} exhibit quantum-like non-commutativity.")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="QND Experiment: Test order effects in moral judgment using Claude API"
    )
    parser.add_argument("--data", required=True, help="Path to CSV file with AITA posts")
    parser.add_argument("--api-key", required=True, help="Anthropic API key")
    parser.add_argument("--n-posts", type=int, default=50, help="Number of posts to test (default: 50)")
    parser.add_argument("--model", default="claude-sonnet-4-20250514", help="Model to use")
    parser.add_argument("--output", default="qnd_results.json", help="Output file for results")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between API calls in seconds")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--stratified", action="store_true", help="Stratify sample by verdict")
    
    args = parser.parse_args()
    
    # Set random seed
    if args.seed:
        random.seed(args.seed)
    
    # Load data
    print(f"Loading data from {args.data}...")
    df = pd.read_csv(args.data)
    print(f"Loaded {len(df)} posts")
    
    # Filter to reasonable length posts
    df = df[df['post_content'].str.len().between(300, 3000)]
    print(f"After length filter: {len(df)} posts")
    
    # Sample posts
    if args.stratified:
        # Stratified sampling by verdict
        sample = []
        per_verdict = args.n_posts // 4
        for verdict in ['NTA', 'YTA', 'ESH', 'NAH']:
            subset = df[df['verdict'] == verdict]
            n = min(per_verdict, len(subset))
            sample.extend(subset.sample(n).to_dict('records'))
        # Fill remainder with YTA (most contested)
        remaining = args.n_posts - len(sample)
        if remaining > 0:
            extra = df[df['verdict'] == 'YTA'].sample(min(remaining, len(df[df['verdict'] == 'YTA'])))
            sample.extend(extra.to_dict('records'))
        random.shuffle(sample)
    else:
        sample = df.sample(min(args.n_posts, len(df))).to_dict('records')
    
    print(f"Selected {len(sample)} posts for testing")
    
    # Initialize API client
    client = anthropic.Anthropic(api_key=args.api_key)
    
    # Run experiment
    results = []
    print(f"\nRunning experiment with {len(sample)} posts...")
    print("This will make {0} API calls (2 per post)".format(len(sample) * 2))
    print("-" * 70)
    
    for i, post in enumerate(sample):
        print(f"[{i+1}/{len(sample)}] Testing: {post.get('post_title', '')[:50]}...")
        
        result = run_single_test(client, post, delay_between_orders=args.delay, model=args.model)
        results.append(result)
        
        # Print inline result
        v_a = result.get('order_A_verdict', 'ERR')
        v_b = result.get('order_B_verdict', 'ERR')
        effect = "✓ EFFECT" if result.get('order_effect') else "  same"
        print(f"         Order A: {v_a}, Order B: {v_b} {effect}")
        
        # Progress stats every 10 posts
        if (i + 1) % 10 == 0:
            valid = [r for r in results if r.get('order_A_verdict') != 'ERROR']
            effects = sum(1 for r in valid if r.get('order_effect'))
            rate = effects / len(valid) if valid else 0
            print(f"         --- Progress: {effects}/{len(valid)} effects ({rate:.1%}) ---")
    
    # Save raw results
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump({
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "n_posts": len(sample),
                "model": args.model,
                "seed": args.seed
            },
            "results": results
        }, f, indent=2)
    print(f"\nRaw results saved to {output_path}")
    
    # Analyze and report
    analysis = analyze_results(results)
    print_report(analysis, results)
    
    # Save analysis
    analysis_path = output_path.with_suffix('.analysis.json')
    with open(analysis_path, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    print(f"\nAnalysis saved to {analysis_path}")


if __name__ == "__main__":
    main()
