#!/usr/bin/env python3
"""
QND Experiment Analysis & Visualization

Analyzes results from qnd_aita_experiment.py and creates visualizations.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Try to import optional visualization libraries
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def load_results(filepath: str) -> dict:
    """Load experiment results from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)


def analyze_order_effects(results: dict) -> dict:
    """Analyze order effect patterns"""
    analysis = {
        "total_posts": 0,
        "order_effects_detected": 0,
        "by_ambiguity": defaultdict(lambda: {"total": 0, "detected": 0}),
        "verdict_changes": []
    }
    
    for post in results.get("posts_results", []):
        analysis["total_posts"] += 1
        order_data = post.get("order_effects", {})
        ambiguity = post.get("ambiguity_level", "unknown")
        
        analysis["by_ambiguity"][ambiguity]["total"] += 1
        
        if order_data.get("order_effect_detected", False):
            analysis["order_effects_detected"] += 1
            analysis["by_ambiguity"][ambiguity]["detected"] += 1
            analysis["verdict_changes"].append({
                "post_id": post.get("post_id"),
                "order_a": order_data.get("verdict_a"),
                "order_b": order_data.get("verdict_b"),
                "ambiguity": ambiguity
            })
    
    # Calculate rates
    if analysis["total_posts"] > 0:
        analysis["detection_rate"] = analysis["order_effects_detected"] / analysis["total_posts"]
    else:
        analysis["detection_rate"] = 0
    
    for amb in analysis["by_ambiguity"]:
        data = analysis["by_ambiguity"][amb]
        if data["total"] > 0:
            data["rate"] = data["detected"] / data["total"]
        else:
            data["rate"] = 0
    
    return analysis


def analyze_interference(results: dict) -> dict:
    """Analyze interference patterns"""
    analysis = {
        "total_posts": 0,
        "effect_counts": {"constructive": 0, "destructive": 0, "none": 0},
        "interference_terms": [],
        "by_ambiguity": defaultdict(list)
    }
    
    for post in results.get("posts_results", []):
        analysis["total_posts"] += 1
        int_data = post.get("interference", {})
        ambiguity = post.get("ambiguity_level", "unknown")
        
        effect = int_data.get("effect", "none")
        analysis["effect_counts"][effect] = analysis["effect_counts"].get(effect, 0) + 1
        
        term = int_data.get("interference_term", 0)
        analysis["interference_terms"].append(term)
        analysis["by_ambiguity"][ambiguity].append(term)
    
    # Calculate statistics
    if analysis["interference_terms"]:
        terms = analysis["interference_terms"]
        analysis["mean_interference"] = sum(terms) / len(terms)
        analysis["max_interference"] = max(terms)
        analysis["min_interference"] = min(terms)
        analysis["variance"] = sum((t - analysis["mean_interference"])**2 for t in terms) / len(terms)
    
    return analysis


def analyze_superposition(results: dict) -> dict:
    """Analyze superposition and entanglement patterns"""
    analysis = {
        "total_posts": 0,
        "superposed_count": 0,
        "entangled_count": 0,
        "branch_counts": [],
        "by_ambiguity": defaultdict(lambda: {"superposed": 0, "entangled": 0, "total": 0})
    }
    
    for post in results.get("posts_results", []):
        analysis["total_posts"] += 1
        q_state = post.get("quantum_state", {})
        ambiguity = post.get("ambiguity_level", "unknown")
        
        analysis["by_ambiguity"][ambiguity]["total"] += 1
        
        if q_state.get("is_superposed", False):
            analysis["superposed_count"] += 1
            analysis["by_ambiguity"][ambiguity]["superposed"] += 1
        
        if q_state.get("is_entangled", False):
            analysis["entangled_count"] += 1
            analysis["by_ambiguity"][ambiguity]["entangled"] += 1
        
        n_branches = q_state.get("n_branches", 1)
        analysis["branch_counts"].append(n_branches)
    
    # Calculate rates
    if analysis["total_posts"] > 0:
        analysis["superposition_rate"] = analysis["superposed_count"] / analysis["total_posts"]
        analysis["entanglement_rate"] = analysis["entangled_count"] / analysis["total_posts"]
    
    if analysis["branch_counts"]:
        analysis["mean_branches"] = sum(analysis["branch_counts"]) / len(analysis["branch_counts"])
    
    return analysis


def generate_text_report(results: dict) -> str:
    """Generate a detailed text report"""
    
    order_analysis = analyze_order_effects(results)
    int_analysis = analyze_interference(results)
    sup_analysis = analyze_superposition(results)
    
    report = []
    report.append("=" * 70)
    report.append("QUANTUM NORMATIVE DYNAMICS - EXPERIMENT ANALYSIS REPORT")
    report.append("=" * 70)
    report.append("")
    report.append(f"Experiment ID: {results.get('experiment_id', 'unknown')}")
    report.append(f"Timestamp: {results.get('timestamp', 'unknown')}")
    report.append(f"Total Posts Analyzed: {results.get('n_posts', 0)}")
    report.append(f"Trials per Test: {results.get('n_trials_per_test', 0)}")
    report.append("")
    
    # Order Effects Section
    report.append("-" * 70)
    report.append("1. ORDER EFFECTS ANALYSIS")
    report.append("-" * 70)
    report.append("")
    report.append("QND Prediction: Question order should affect moral judgments")
    report.append("                (non-commuting observables)")
    report.append("")
    report.append(f"Detection Rate: {order_analysis['detection_rate']*100:.1f}%")
    report.append(f"Posts with Order Effects: {order_analysis['order_effects_detected']}/{order_analysis['total_posts']}")
    report.append("")
    report.append("By Ambiguity Level:")
    for amb, data in order_analysis["by_ambiguity"].items():
        report.append(f"  {amb}: {data['detected']}/{data['total']} ({data['rate']*100:.1f}%)")
    report.append("")
    
    if order_analysis["verdict_changes"]:
        report.append("Verdict Changes Observed:")
        for change in order_analysis["verdict_changes"][:5]:  # Show first 5
            report.append(f"  Post {change['post_id']}: {change['order_a']} → {change['order_b']}")
    report.append("")
    
    qnd_support = "✓ SUPPORTS QND" if order_analysis['detection_rate'] > 0.2 else "○ WEAK/INCONCLUSIVE"
    report.append(f"Assessment: {qnd_support}")
    report.append("")
    
    # Interference Section
    report.append("-" * 70)
    report.append("2. INTERFERENCE EFFECTS ANALYSIS")
    report.append("-" * 70)
    report.append("")
    report.append("QND Prediction: Multiple reasoning frameworks should interfere,")
    report.append("                not simply add (constructive/destructive effects)")
    report.append("")
    report.append("Effect Distribution:")
    total = int_analysis["total_posts"]
    for effect, count in int_analysis["effect_counts"].items():
        pct = (count/total*100) if total > 0 else 0
        bar = "█" * int(pct/5) + "░" * (20 - int(pct/5))
        report.append(f"  {effect:12s}: {bar} {pct:5.1f}% ({count})")
    report.append("")
    
    if int_analysis.get("mean_interference") is not None:
        report.append("Interference Term Statistics:")
        report.append(f"  Mean: {int_analysis['mean_interference']:+.3f}")
        report.append(f"  Range: [{int_analysis['min_interference']:+.3f}, {int_analysis['max_interference']:+.3f}]")
        report.append(f"  Variance: {int_analysis['variance']:.4f}")
    report.append("")
    
    has_interference = (int_analysis["effect_counts"].get("constructive", 0) + 
                        int_analysis["effect_counts"].get("destructive", 0))
    interference_rate = has_interference / total if total > 0 else 0
    qnd_support = "✓ SUPPORTS QND" if interference_rate > 0.3 else "○ WEAK/INCONCLUSIVE"
    report.append(f"Assessment: {qnd_support}")
    report.append("")
    
    # Superposition Section
    report.append("-" * 70)
    report.append("3. SUPERPOSITION & ENTANGLEMENT ANALYSIS")
    report.append("-" * 70)
    report.append("")
    report.append("QND Prediction: Moral situations exist in superposition of states")
    report.append("                before measurement (judgment)")
    report.append("")
    report.append(f"Superposition Rate: {sup_analysis.get('superposition_rate', 0)*100:.1f}%")
    report.append(f"Entanglement Rate: {sup_analysis.get('entanglement_rate', 0)*100:.1f}%")
    report.append(f"Mean Branches per Case: {sup_analysis.get('mean_branches', 1):.2f}")
    report.append("")
    report.append("By Ambiguity Level:")
    for amb, data in sup_analysis["by_ambiguity"].items():
        sup_rate = data['superposed']/data['total']*100 if data['total'] > 0 else 0
        ent_rate = data['entangled']/data['total']*100 if data['total'] > 0 else 0
        report.append(f"  {amb}: Superposed={sup_rate:.1f}%, Entangled={ent_rate:.1f}%")
    report.append("")
    
    qnd_support = "✓ SUPPORTS QND" if sup_analysis.get('superposition_rate', 0) > 0.5 else "○ WEAK/INCONCLUSIVE"
    report.append(f"Assessment: {qnd_support}")
    report.append("")
    
    # Overall Assessment
    report.append("=" * 70)
    report.append("OVERALL QND ASSESSMENT")
    report.append("=" * 70)
    report.append("")
    
    # Count supporting evidence
    support_count = 0
    if order_analysis['detection_rate'] > 0.2:
        support_count += 1
    if interference_rate > 0.3:
        support_count += 1
    if sup_analysis.get('superposition_rate', 0) > 0.5:
        support_count += 1
    if sup_analysis.get('entanglement_rate', 0) > 0.1:
        support_count += 1
    
    report.append(f"QND Predictions Supported: {support_count}/4")
    report.append("")
    
    if support_count >= 3:
        report.append("CONCLUSION: Strong support for Quantum Normative Dynamics")
        report.append("            Moral reasoning shows quantum-like properties")
    elif support_count >= 2:
        report.append("CONCLUSION: Moderate support for QND")
        report.append("            Some quantum effects detected, more data needed")
    else:
        report.append("CONCLUSION: Weak or no support for QND")
        report.append("            Classical models may suffice for this data")
    report.append("")
    
    report.append("-" * 70)
    report.append("RECOMMENDATIONS FOR FUTURE EXPERIMENTS")
    report.append("-" * 70)
    report.append("")
    report.append("1. Increase sample size (n > 100 posts)")
    report.append("2. Include more ambiguous/contested cases")
    report.append("3. Test Bell inequality violations for entanglement")
    report.append("4. Measure decoherence rates over time")
    report.append("5. Compare with human annotator disagreement rates")
    report.append("")
    
    return "\n".join(report)


def create_visualizations(results: dict, output_dir: str = "."):
    """Create visualization plots (requires matplotlib)"""
    
    if not HAS_MATPLOTLIB:
        print("matplotlib not available. Skipping visualizations.")
        return
    
    output_path = Path(output_dir)
    
    # Prepare data
    order_analysis = analyze_order_effects(results)
    int_analysis = analyze_interference(results)
    sup_analysis = analyze_superposition(results)
    
    # Figure 1: Overview Dashboard
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle("QND Experiment Results Dashboard", fontsize=14, fontweight='bold')
    
    # 1a: Order Effects by Ambiguity
    ax = axes[0, 0]
    ambiguity_levels = list(order_analysis["by_ambiguity"].keys())
    rates = [order_analysis["by_ambiguity"][a]["rate"] * 100 for a in ambiguity_levels]
    colors = ['#2ecc71' if r > 20 else '#e74c3c' for r in rates]
    bars = ax.bar(ambiguity_levels, rates, color=colors, edgecolor='black')
    ax.axhline(y=20, color='gray', linestyle='--', label='QND threshold')
    ax.set_ylabel("Order Effect Detection Rate (%)")
    ax.set_xlabel("Ambiguity Level")
    ax.set_title("Order Effects by Ambiguity")
    ax.legend()
    ax.set_ylim(0, 100)
    
    # 1b: Interference Effect Distribution
    ax = axes[0, 1]
    effects = list(int_analysis["effect_counts"].keys())
    counts = [int_analysis["effect_counts"][e] for e in effects]
    colors = ['#2ecc71', '#e74c3c', '#95a5a6']
    ax.pie(counts, labels=effects, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.set_title("Interference Effect Distribution")
    
    # 1c: Interference Terms Histogram
    ax = axes[1, 0]
    terms = int_analysis["interference_terms"]
    if terms:
        ax.hist(terms, bins=10, color='#3498db', edgecolor='black', alpha=0.7)
        ax.axvline(x=0, color='red', linestyle='--', label='No interference')
        ax.axvline(x=sum(terms)/len(terms), color='green', linestyle='-', label=f'Mean={sum(terms)/len(terms):.2f}')
        ax.set_xlabel("Interference Term")
        ax.set_ylabel("Frequency")
        ax.set_title("Distribution of Interference Terms")
        ax.legend()
    
    # 1d: Superposition Summary
    ax = axes[1, 1]
    metrics = ['Superposition\nRate', 'Entanglement\nRate', 'Order Effect\nRate']
    values = [
        sup_analysis.get('superposition_rate', 0) * 100,
        sup_analysis.get('entanglement_rate', 0) * 100,
        order_analysis['detection_rate'] * 100
    ]
    thresholds = [50, 10, 20]  # QND support thresholds
    
    x = range(len(metrics))
    bars = ax.bar(x, values, color='#3498db', edgecolor='black')
    for i, (v, t) in enumerate(zip(values, thresholds)):
        if v >= t:
            bars[i].set_color('#2ecc71')
        else:
            bars[i].set_color('#e74c3c')
    
    # Add threshold lines
    for i, t in enumerate(thresholds):
        ax.hlines(y=t, xmin=i-0.4, xmax=i+0.4, color='gray', linestyle='--', linewidth=2)
    
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.set_ylabel("Rate (%)")
    ax.set_title("QND Metrics vs Thresholds")
    ax.set_ylim(0, 100)
    
    # Add legend
    green_patch = mpatches.Patch(color='#2ecc71', label='Supports QND')
    red_patch = mpatches.Patch(color='#e74c3c', label='Below threshold')
    ax.legend(handles=[green_patch, red_patch], loc='upper right')
    
    plt.tight_layout()
    plt.savefig(output_path / "qnd_dashboard.png", dpi=150)
    print(f"Saved dashboard to {output_path / 'qnd_dashboard.png'}")
    
    # Figure 2: Per-Post Results
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    posts = results.get("posts_results", [])
    post_ids = [p.get("post_id", f"post_{i}")[:10] for i, p in enumerate(posts)]
    
    # 2a: Order effects per post
    ax = axes[0]
    order_detected = [1 if p.get("order_effects", {}).get("order_effect_detected") else 0 for p in posts]
    colors = ['#2ecc71' if d else '#e74c3c' for d in order_detected]
    ax.bar(range(len(posts)), order_detected, color=colors)
    ax.set_xticks(range(len(posts)))
    ax.set_xticklabels(post_ids, rotation=45, ha='right')
    ax.set_ylabel("Order Effect Detected")
    ax.set_title("Order Effects by Post")
    ax.set_ylim(0, 1.2)
    
    # 2b: Number of superposition branches per post
    ax = axes[1]
    n_branches = [p.get("quantum_state", {}).get("n_branches", 1) for p in posts]
    ambiguity = [p.get("ambiguity_level", "unknown") for p in posts]
    color_map = {"low": "#3498db", "medium": "#f39c12", "high": "#e74c3c", "unknown": "#95a5a6"}
    colors = [color_map.get(a, "#95a5a6") for a in ambiguity]
    
    ax.bar(range(len(posts)), n_branches, color=colors)
    ax.set_xticks(range(len(posts)))
    ax.set_xticklabels(post_ids, rotation=45, ha='right')
    ax.set_ylabel("Number of Branches")
    ax.set_title("Superposition Branches by Post")
    
    # Add legend
    handles = [mpatches.Patch(color=c, label=l) for l, c in color_map.items()]
    ax.legend(handles=handles, title="Ambiguity", loc='upper right')
    
    plt.tight_layout()
    plt.savefig(output_path / "qnd_per_post.png", dpi=150)
    print(f"Saved per-post analysis to {output_path / 'qnd_per_post.png'}")
    
    plt.close('all')


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_qnd_results.py <results.json> [output_dir]")
        print("\nThis script analyzes results from qnd_aita_experiment.py")
        sys.exit(1)
    
    results_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    
    print(f"Loading results from {results_file}...")
    results = load_results(results_file)
    
    # Generate text report
    print("\nGenerating analysis report...")
    report = generate_text_report(results)
    print(report)
    
    # Save report
    report_path = Path(output_dir) / "qnd_analysis_report.txt"
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"\nReport saved to {report_path}")
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    create_visualizations(results, output_dir)
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
