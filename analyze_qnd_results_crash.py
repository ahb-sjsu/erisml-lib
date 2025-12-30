#!/usr/bin/env python3
"""
QND Results Analyzer - Process already-downloaded batch results

Usage:
    python analyze_qnd_results.py --results-dir ./qnd_bell_batch_3-lang_results
"""

import json
import math
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class CHSHResult:
    scenario: str
    alpha_lang: str
    beta_lang: str
    is_crosslingual: bool
    E_pp: float
    E_ps: float
    E_sp: float
    E_ss: float
    S: float
    std_error: float
    n_measurements: int
    violation: bool
    significance: float


def load_results(results_dir: Path) -> tuple:
    """Load specs and results from directory."""
    
    # Find the specs file
    specs_files = list(results_dir.glob("*_specs.json"))
    if not specs_files:
        raise FileNotFoundError(f"No specs file found in {results_dir}")
    
    specs_path = specs_files[0]
    batch_id = specs_path.stem.replace("_specs", "")
    
    print(f"Found batch: {batch_id}")
    
    # Load specs
    with open(specs_path) as f:
        specs_data = json.load(f)
    specs_by_id = {s["custom_id"]: s for s in specs_data}
    
    print(f"Loaded {len(specs_by_id)} specs")
    
    # Try to load results file
    results_path = results_dir / f"{batch_id}_results.json"
    if results_path.exists():
        with open(results_path) as f:
            results = json.load(f)
        print(f"Loaded {len(results)} results from {results_path}")
        return specs_by_id, results
    
    print("No results file found - you may need to re-run with --mode results")
    return specs_by_id, {}


def calculate_chsh(results: Dict[str, Any], specs_by_id: Dict) -> List[CHSHResult]:
    """Calculate CHSH S values from results."""
    
    configs = {}
    
    for custom_id, data in results.items():
        spec = data.get("spec", specs_by_id.get(custom_id, {}))
        if not spec:
            continue
            
        scenario = spec["scenario"]
        
        # Handle various language format strings
        alpha_lang = str(spec["alpha_lang"])
        beta_lang = str(spec["beta_lang"])
        
        # Normalize language strings
        for old, new in [("Language.ENGLISH", "en"), ("Language.JAPANESE", "ja"), 
                         ("Language.MANDARIN", "zh"), ("Language.CHINESE", "zh"),
                         ("Language.SPANISH", "es"), ("Language.GERMAN", "de"),
                         ("Language.ARABIC", "ar")]:
            alpha_lang = alpha_lang.replace(old, new)
            beta_lang = beta_lang.replace(old, new)
        
        is_cross = alpha_lang != beta_lang
        
        config_key = (scenario, alpha_lang, beta_lang, is_cross)
        if config_key not in configs:
            configs[config_key] = {
                ("primary", "primary"): {"alpha": {}, "beta": {}},
                ("primary", "secondary"): {"alpha": {}, "beta": {}},
                ("secondary", "primary"): {"alpha": {}, "beta": {}},
                ("secondary", "secondary"): {"alpha": {}, "beta": {}},
            }
        
        # Parse custom_id to get trial and axes
        parts = custom_id.split("_")
        trial_idx = None
        axes = None
        for i, p in enumerate(parts):
            if p.isdigit():
                trial_idx = int(p)
                if i + 1 < len(parts) and len(parts[i+1]) == 2 and parts[i+1] in ["pp", "ps", "sp", "ss"]:
                    axes = parts[i+1]
                break
        
        if trial_idx is None or axes is None:
            continue
        
        axis_map = {"p": "primary", "s": "secondary"}
        alpha_axis = axis_map.get(axes[0])
        beta_axis = axis_map.get(axes[1])
        
        if not alpha_axis or not beta_axis:
            continue
        
        setting = (alpha_axis, beta_axis)
        subject = spec["subject"]
        trial_key = f"{trial_idx}_{axes}"
        
        configs[config_key][setting][subject][trial_key] = data["verdict"]
    
    # Calculate CHSH values
    chsh_results = []
    
    for config_key, settings in configs.items():
        scenario, alpha_lang, beta_lang, is_cross = config_key
        
        correlations = {}
        for setting in [("primary", "primary"), ("primary", "secondary"),
                       ("secondary", "primary"), ("secondary", "secondary")]:
            correlations[setting] = []
            
            alpha_data = settings[setting]["alpha"]
            beta_data = settings[setting]["beta"]
            
            for trial_key in alpha_data:
                if trial_key in beta_data:
                    corr = alpha_data[trial_key] * beta_data[trial_key]
                    correlations[setting].append(corr)
        
        def calc_E(corrs):
            if not corrs:
                return 0.0, float('inf')
            mean = sum(corrs) / len(corrs)
            var = sum((c - mean)**2 for c in corrs) / len(corrs) if len(corrs) > 1 else 1.0
            se = math.sqrt(var / len(corrs))
            return mean, se
        
        E_pp, se_pp = calc_E(correlations[("primary", "primary")])
        E_ps, se_ps = calc_E(correlations[("primary", "secondary")])
        E_sp, se_sp = calc_E(correlations[("secondary", "primary")])
        E_ss, se_ss = calc_E(correlations[("secondary", "secondary")])
        
        S = E_pp - E_ps + E_sp + E_ss
        std_error = math.sqrt(se_pp**2 + se_ps**2 + se_sp**2 + se_ss**2)
        
        n_meas = sum(len(c) for c in correlations.values())
        violation = abs(S) > 2.0
        significance = (abs(S) - 2.0) / std_error if std_error > 0 and violation else 0.0
        
        chsh_results.append(CHSHResult(
            scenario=scenario,
            alpha_lang=alpha_lang,
            beta_lang=beta_lang,
            is_crosslingual=is_cross,
            E_pp=E_pp, E_ps=E_ps, E_sp=E_sp, E_ss=E_ss,
            S=S,
            std_error=std_error,
            n_measurements=n_meas,
            violation=violation,
            significance=significance
        ))
    
    return chsh_results


def get_lang_name(lang_str: str) -> str:
    """Convert language code to display name."""
    lang_str = str(lang_str)
    
    # Handle "Language.ENGLISH" format
    if "ENGLISH" in lang_str: return "English"
    if "JAPANESE" in lang_str: return "日本語"
    if "MANDARIN" in lang_str or "CHINESE" in lang_str: return "中文"
    if "SPANISH" in lang_str: return "Español"
    if "ARABIC" in lang_str: return "العربية"
    if "GERMAN" in lang_str: return "Deutsch"
    
    # Handle short codes
    names = {"en": "English", "ja": "日本語", "zh": "中文", 
             "es": "Español", "ar": "العربية", "de": "Deutsch"}
    return names.get(lang_str, lang_str)


def print_report(results: List[CHSHResult]):
    """Print comprehensive report."""
    
    print("\n" + "=" * 70)
    print("QND BATCH BELL TEST RESULTS")
    print("=" * 70)
    print("\nCHSH: S = E(a,b) - E(a,b') + E(a',b) + E(a',b')")
    print("Classical limit: |S| ≤ 2")
    print("Quantum limit: |S| ≤ 2√2 ≈ 2.83")
    print("-" * 70)
    
    mono = [r for r in results if not r.is_crosslingual]
    cross = [r for r in results if r.is_crosslingual]
    
    if mono:
        print("\n### MONOLINGUAL TESTS ###")
        for r in sorted(mono, key=lambda x: (x.scenario, x.alpha_lang)):
            lang = get_lang_name(r.alpha_lang)
            print(f"\n[{r.scenario}] in {lang}")
            print(f"  E(a,b)={r.E_pp:+.3f}  E(a,b')={r.E_ps:+.3f}  E(a',b)={r.E_sp:+.3f}  E(a',b')={r.E_ss:+.3f}")
            print(f"  S = {r.S:+.3f} ± {r.std_error:.3f}  (n={r.n_measurements})")
            if r.violation:
                print(f"  ★ VIOLATION at {r.significance:.1f}σ")
            else:
                print(f"  No violation (|S| = {abs(r.S):.3f})")
    
    if cross:
        print("\n" + "=" * 70)
        print("### CROSS-LINGUAL TESTS ###")
        print("(If |S| > 2 here, correlation exists at SEMANTIC layer)")
        print("=" * 70)
        for r in sorted(cross, key=lambda x: (x.scenario, x.alpha_lang)):
            a_lang = get_lang_name(r.alpha_lang)
            b_lang = get_lang_name(r.beta_lang)
            print(f"\n[{r.scenario}] α={a_lang}, β={b_lang}")
            print(f"  E(a,b)={r.E_pp:+.3f}  E(a,b')={r.E_ps:+.3f}  E(a',b)={r.E_sp:+.3f}  E(a',b')={r.E_ss:+.3f}")
            print(f"  S = {r.S:+.3f} ± {r.std_error:.3f}  (n={r.n_measurements})")
            if r.violation:
                print(f"  ★★★ CROSS-LINGUAL VIOLATION at {r.significance:.1f}σ ★★★")
            else:
                print(f"  No violation (|S| = {abs(r.S):.3f})")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    all_violations = [r for r in results if r.violation]
    cross_violations = [r for r in cross if r.violation]
    
    if results:
        max_S = max(abs(r.S) for r in results)
        max_sig = max(r.significance for r in results) if any(r.violation for r in results) else 0
        
        print(f"\nTotal tests: {len(results)}")
        print(f"  Monolingual: {len(mono)}")
        print(f"  Cross-lingual: {len(cross)}")
        print(f"\nViolations (|S| > 2): {len(all_violations)}")
        print(f"  Cross-lingual violations: {len(cross_violations)}")
        print(f"\nMax |S|: {max_S:.3f}")
        print(f"Max significance: {max_sig:.1f}σ")
        
        if cross_violations:
            print("\n" + "★" * 50)
            print("CROSS-LINGUAL BELL VIOLATION DETECTED!")
            print("The correlation exists at the SEMANTIC layer.")
            print("Evidence for Universal Grammar of Ethics.")
            print("★" * 50)
        elif all_violations:
            print("\n⚠ Bell violations detected in monolingual tests only.")
            print("Could be linguistic artifact - cross-lingual test needed for confirmation.")
        else:
            print("\n✗ No Bell violations detected.")
            print("Moral judgments appear to follow classical probability bounds.")


def main():
    parser = argparse.ArgumentParser(description="Analyze QND Bell Test results")
    parser.add_argument("--results-dir", required=True, help="Directory with batch results")
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    
    if not results_dir.exists():
        print(f"Error: Directory not found: {results_dir}")
        return
    
    print(f"Loading results from {results_dir}...")
    
    specs_by_id, results = load_results(results_dir)
    
    if not results:
        print("\nNo results to analyze. The batch may have completed but results weren't saved.")
        print("Check if there's a *_results.json file in the directory.")
        return
    
    print(f"\nCalculating CHSH values...")
    chsh_results = calculate_chsh(results, specs_by_id)
    
    if not chsh_results:
        print("Error: Could not calculate CHSH values. Check data format.")
        return
    
    print_report(chsh_results)
    
    # Save summary
    summary_path = results_dir / "chsh_summary.json"
    summary = {
        "total_tests": len(chsh_results),
        "violations": len([r for r in chsh_results if r.violation]),
        "cross_lingual_violations": len([r for r in chsh_results if r.violation and r.is_crosslingual]),
        "max_S": max(abs(r.S) for r in chsh_results),
        "results": [
            {
                "scenario": r.scenario,
                "alpha_lang": r.alpha_lang,
                "beta_lang": r.beta_lang,
                "is_crosslingual": r.is_crosslingual,
                "S": r.S,
                "violation": r.violation,
                "significance": r.significance
            }
            for r in chsh_results
        ]
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary saved to {summary_path}")


if __name__ == "__main__":
    main()
