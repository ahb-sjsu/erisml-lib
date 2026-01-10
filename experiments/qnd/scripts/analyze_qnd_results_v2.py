#!/usr/bin/env python3
"""
QND Results Analyzer v2.0 - Fixed and Improved

Fixes from v1:
- Robust language string normalization (handles all enum formats)
- Better custom_id parsing with fallback strategies
- Debug mode for troubleshooting data format issues
- Support for multiple results file formats
- Graceful handling of missing/malformed data
- Cross-model comparison support

Usage:
    python analyze_qnd_results_v2.py --results-dir ./qnd_results
    python analyze_qnd_results_v2.py --results-dir ./qnd_results --debug
    python analyze_qnd_results_v2.py --compare dir1 dir2 dir3  # Compare multiple models
"""

import json
import math
import argparse
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict


@dataclass
class CHSHResult:
    """Result of a single CHSH Bell test."""

    scenario: str
    alpha_lang: str
    beta_lang: str
    is_crosslingual: bool
    E_pp: float  # E(a,b) - primary/primary
    E_ps: float  # E(a,b') - primary/secondary
    E_sp: float  # E(a',b) - secondary/primary
    E_ss: float  # E(a',b') - secondary/secondary
    S: float  # CHSH S value
    std_error: float
    n_measurements: int
    violation: bool
    significance: float
    model: str = "unknown"  # For cross-model comparison


def normalize_language(lang_str: str) -> str:
    """
    Normalize language strings to ISO codes.
    Handles: 'en', 'Language.ENGLISH', 'ENGLISH', '<Language.ENGLISH: "en">', etc.
    """
    if not lang_str:
        return "unknown"

    lang_str = str(lang_str).strip()

    # Direct ISO codes
    if lang_str.lower() in ["en", "english"]:
        return "en"
    if lang_str.lower() in ["ja", "japanese", "jp"]:
        return "ja"
    if lang_str.lower() in ["zh", "mandarin", "chinese", "zh-cn", "zh-tw"]:
        return "zh"
    if lang_str.lower() in ["es", "spanish", "español"]:
        return "es"
    if lang_str.lower() in ["de", "german", "deutsch"]:
        return "de"
    if lang_str.lower() in ["ar", "arabic"]:
        return "ar"
    if lang_str.lower() in ["fr", "french", "français"]:
        return "fr"

    # Handle enum-style strings: "Language.ENGLISH" or "<Language.ENGLISH: 'en'>"
    lang_upper = lang_str.upper()
    if "ENGLISH" in lang_upper:
        return "en"
    if "JAPANESE" in lang_upper:
        return "ja"
    if "MANDARIN" in lang_upper or "CHINESE" in lang_upper:
        return "zh"
    if "SPANISH" in lang_upper:
        return "es"
    if "GERMAN" in lang_upper:
        return "de"
    if "ARABIC" in lang_upper:
        return "ar"
    if "FRENCH" in lang_upper:
        return "fr"

    # Try to extract quoted value: <Language.ENGLISH: "en">
    match = re.search(r'["\'](\w{2})["\']', lang_str)
    if match:
        return match.group(1).lower()

    # Last resort: return first two chars if they look like a code
    if len(lang_str) >= 2 and lang_str[:2].isalpha():
        return lang_str[:2].lower()

    return "unknown"


def get_lang_display_name(lang_code: str) -> str:
    """Convert ISO code to display name."""
    names = {
        "en": "English",
        "ja": "日本語",
        "zh": "中文",
        "es": "Español",
        "de": "Deutsch",
        "ar": "العربية",
        "fr": "Français",
        "unknown": "Unknown",
    }
    return names.get(lang_code, lang_code)


def parse_custom_id(
    custom_id: str, debug: bool = False
) -> Optional[Tuple[int, str, str]]:
    """
    Parse custom_id to extract trial index, axes, and subject.

    Expected formats:
    - m_scenario_lang_TRIAL_AXES_SUBJECT_salt
    - x_scenario_langs_TRIAL_AXES_SUBJECT_salt
    - scenario_TRIAL_AXES_SUBJECT

    Returns: (trial_idx, axes, subject) or None if parsing fails
    """
    parts = custom_id.split("_")

    if debug:
        print(f"  Parsing custom_id: {custom_id}")
        print(f"  Parts: {parts}")

    # Strategy 1: Find numeric trial index, then look for axes pattern
    for i, part in enumerate(parts):
        if part.isdigit():
            trial_idx = int(part)

            # Look for axes in next position
            if i + 1 < len(parts):
                potential_axes = parts[i + 1].lower()
                if potential_axes in ["pp", "ps", "sp", "ss"]:
                    # Look for subject (alpha/beta) in next position
                    subject = None
                    if i + 2 < len(parts):
                        potential_subject = parts[i + 2].lower()
                        if potential_subject in ["alpha", "beta", "a", "b"]:
                            subject = (
                                "alpha"
                                if potential_subject in ["alpha", "a"]
                                else "beta"
                            )

                    if debug:
                        print(
                            f"  Found: trial={trial_idx}, axes={potential_axes}, subject={subject}"
                        )

                    return (trial_idx, potential_axes, subject)

    # Strategy 2: Look for axes pattern anywhere
    for i, part in enumerate(parts):
        if part.lower() in ["pp", "ps", "sp", "ss"]:
            axes = part.lower()
            # Try to find trial number before it
            trial_idx = 0
            for j in range(i - 1, -1, -1):
                if parts[j].isdigit():
                    trial_idx = int(parts[j])
                    break

            # Try to find subject after it
            subject = None
            if i + 1 < len(parts):
                potential_subject = parts[i + 1].lower()
                if potential_subject in ["alpha", "beta", "a", "b"]:
                    subject = "alpha" if potential_subject in ["alpha", "a"] else "beta"

            if debug:
                print(
                    f"  Fallback found: trial={trial_idx}, axes={axes}, subject={subject}"
                )

            return (trial_idx, axes, subject)

    if debug:
        print(f"  Failed to parse custom_id")

    return None


def load_results(results_dir: Path, debug: bool = False) -> Tuple[Dict, Dict, str]:
    """
    Load specs and results from directory.
    Returns: (specs_by_id, results, model_name)
    """
    results_dir = Path(results_dir)

    # Try to determine model name from directory
    model_name = results_dir.name
    if "claude" in model_name.lower():
        model_name = "Claude"
    elif "gpt" in model_name.lower():
        model_name = "GPT-4"
    elif "gemini" in model_name.lower():
        model_name = "Gemini"
    elif "llama" in model_name.lower():
        model_name = "Llama"

    # Find specs file
    specs_files = list(results_dir.glob("*_specs.json")) + list(
        results_dir.glob("*specs*.json")
    )
    if not specs_files:
        print(f"Warning: No specs file found in {results_dir}")
        specs_by_id = {}
    else:
        specs_path = specs_files[0]
        batch_id = specs_path.stem.replace("_specs", "")
        print(f"Found batch: {batch_id}")

        with open(specs_path, encoding="utf-8") as f:
            specs_data = json.load(f)

        # Handle both list and dict formats
        if isinstance(specs_data, list):
            specs_by_id = {
                s.get("custom_id", str(i)): s for i, s in enumerate(specs_data)
            }
        else:
            specs_by_id = specs_data

        print(f"Loaded {len(specs_by_id)} specs")

        if debug and specs_by_id:
            sample_key = next(iter(specs_by_id))
            print(f"Sample spec key: {sample_key}")
            print(
                f"Sample spec: {json.dumps(specs_by_id[sample_key], indent=2, default=str)[:500]}"
            )

    # Find results file
    results_files = (
        list(results_dir.glob("*_results.json"))
        + list(results_dir.glob("*results*.json"))
        + list(results_dir.glob("*.json"))
    )

    # Filter out specs files
    results_files = [f for f in results_files if "spec" not in f.name.lower()]

    if not results_files:
        print(f"No results file found in {results_dir}")
        return specs_by_id, {}, model_name

    # Try each results file
    for results_path in results_files:
        try:
            with open(results_path, encoding="utf-8") as f:
                results = json.load(f)

            if isinstance(results, dict) and len(results) > 0:
                print(f"Loaded {len(results)} results from {results_path.name}")

                if debug:
                    sample_key = next(iter(results))
                    print(f"Sample result key: {sample_key}")
                    print(
                        f"Sample result: {json.dumps(results[sample_key], indent=2, default=str)[:500]}"
                    )

                return specs_by_id, results, model_name

        except (json.JSONDecodeError, KeyError) as e:
            if debug:
                print(f"Failed to load {results_path}: {e}")
            continue

    print("No valid results file found")
    return specs_by_id, {}, model_name


def calculate_chsh(
    results: Dict[str, Any],
    specs_by_id: Dict,
    model_name: str = "unknown",
    debug: bool = False,
) -> List[CHSHResult]:
    """Calculate CHSH S values from results."""

    # Group results by configuration
    # config_key = (scenario, alpha_lang, beta_lang)
    # setting = (alpha_axis, beta_axis)
    # For each setting, we need alpha and beta verdicts per trial

    configs = defaultdict(
        lambda: {
            ("primary", "primary"): {"alpha": {}, "beta": {}},
            ("primary", "secondary"): {"alpha": {}, "beta": {}},
            ("secondary", "primary"): {"alpha": {}, "beta": {}},
            ("secondary", "secondary"): {"alpha": {}, "beta": {}},
        }
    )

    parse_failures = 0
    parse_successes = 0

    for custom_id, data in results.items():
        # Get spec (may be embedded in data or separate)
        spec = data.get("spec", specs_by_id.get(custom_id, {}))

        if not spec:
            if debug:
                print(f"No spec found for {custom_id}")
            parse_failures += 1
            continue

        # Extract and normalize fields
        scenario = spec.get("scenario", "unknown")
        alpha_lang = normalize_language(spec.get("alpha_lang", ""))
        beta_lang = normalize_language(spec.get("beta_lang", ""))
        subject = spec.get("subject", "").lower()

        # Parse custom_id for trial info
        parsed = parse_custom_id(custom_id, debug=debug and parse_successes < 3)
        if parsed is None:
            parse_failures += 1
            continue

        trial_idx, axes, parsed_subject = parsed

        # Use subject from spec if available, otherwise from custom_id
        if not subject and parsed_subject:
            subject = parsed_subject

        if subject not in ["alpha", "beta"]:
            if debug:
                print(f"Invalid subject '{subject}' for {custom_id}")
            parse_failures += 1
            continue

        # Get verdict
        verdict = data.get("verdict")
        if verdict is None:
            if debug:
                print(f"No verdict for {custom_id}")
            parse_failures += 1
            continue

        # Map axes to settings
        axis_map = {"p": "primary", "s": "secondary"}
        alpha_axis = axis_map.get(axes[0])
        beta_axis = axis_map.get(axes[1])

        if not alpha_axis or not beta_axis:
            parse_failures += 1
            continue

        # Store result
        is_cross = alpha_lang != beta_lang
        config_key = (scenario, alpha_lang, beta_lang, is_cross)
        setting = (alpha_axis, beta_axis)
        trial_key = f"{trial_idx}_{axes}"

        configs[config_key][setting][subject][trial_key] = verdict
        parse_successes += 1

    print(f"Parsed {parse_successes} results, {parse_failures} failures")

    if debug:
        print(f"\nConfigurations found: {len(configs)}")
        for key in list(configs.keys())[:3]:
            print(f"  {key}")

    # Calculate CHSH for each configuration
    chsh_results = []

    for config_key, settings in configs.items():
        scenario, alpha_lang, beta_lang, is_cross = config_key

        correlations = {}
        for setting in [
            ("primary", "primary"),
            ("primary", "secondary"),
            ("secondary", "primary"),
            ("secondary", "secondary"),
        ]:
            correlations[setting] = []

            alpha_data = settings[setting]["alpha"]
            beta_data = settings[setting]["beta"]

            # Match trials
            for trial_key in alpha_data:
                if trial_key in beta_data:
                    # Correlation: product of verdicts (-1 or +1)
                    corr = alpha_data[trial_key] * beta_data[trial_key]
                    correlations[setting].append(corr)

        # Calculate E values with standard errors
        def calc_E(corrs):
            if not corrs:
                return 0.0, float("inf")
            n = len(corrs)
            mean = sum(corrs) / n
            if n > 1:
                var = sum((c - mean) ** 2 for c in corrs) / (n - 1)  # Sample variance
                se = math.sqrt(var / n)
            else:
                se = 1.0  # Maximum uncertainty for single measurement
            return mean, se

        E_pp, se_pp = calc_E(correlations[("primary", "primary")])
        E_ps, se_ps = calc_E(correlations[("primary", "secondary")])
        E_sp, se_sp = calc_E(correlations[("secondary", "primary")])
        E_ss, se_ss = calc_E(correlations[("secondary", "secondary")])

        # CHSH S value: S = E(a,b) - E(a,b') + E(a',b) + E(a',b')
        S = E_pp - E_ps + E_sp + E_ss

        # Propagate standard errors
        std_error = math.sqrt(se_pp**2 + se_ps**2 + se_sp**2 + se_ss**2)

        n_meas = sum(len(c) for c in correlations.values())
        violation = abs(S) > 2.0

        # Significance: how many standard deviations above classical bound
        if std_error > 0 and std_error != float("inf"):
            significance = (abs(S) - 2.0) / std_error if violation else 0.0
        else:
            significance = 0.0

        chsh_results.append(
            CHSHResult(
                scenario=scenario,
                alpha_lang=alpha_lang,
                beta_lang=beta_lang,
                is_crosslingual=is_cross,
                E_pp=E_pp,
                E_ps=E_ps,
                E_sp=E_sp,
                E_ss=E_ss,
                S=S,
                std_error=std_error,
                n_measurements=n_meas,
                violation=violation,
                significance=significance,
                model=model_name,
            )
        )

    return chsh_results


def print_report(results: List[CHSHResult], title: str = "QND BELL TEST RESULTS"):
    """Print comprehensive report."""

    if not results:
        print("\nNo results to report.")
        return

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
    print("\nCHSH: S = E(a,b) - E(a,b') + E(a',b) + E(a',b')")
    print("Classical limit: |S| ≤ 2")
    print("Quantum limit: |S| ≤ 2√2 ≈ 2.83")
    print("-" * 70)

    mono = [r for r in results if not r.is_crosslingual]
    cross = [r for r in results if r.is_crosslingual]

    if mono:
        print("\n### MONOLINGUAL TESTS ###")
        for r in sorted(mono, key=lambda x: (x.model, x.scenario, x.alpha_lang)):
            lang = get_lang_display_name(r.alpha_lang)
            model_str = f"[{r.model}] " if r.model != "unknown" else ""
            print(f"\n{model_str}[{r.scenario}] in {lang}")
            print(
                f"  E(a,b)={r.E_pp:+.3f}  E(a,b')={r.E_ps:+.3f}  E(a',b)={r.E_sp:+.3f}  E(a',b')={r.E_ss:+.3f}"
            )
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
        for r in sorted(cross, key=lambda x: (x.model, x.scenario, x.alpha_lang)):
            a_lang = get_lang_display_name(r.alpha_lang)
            b_lang = get_lang_display_name(r.beta_lang)
            model_str = f"[{r.model}] " if r.model != "unknown" else ""
            print(f"\n{model_str}[{r.scenario}] α={a_lang}, β={b_lang}")
            print(
                f"  E(a,b)={r.E_pp:+.3f}  E(a,b')={r.E_ps:+.3f}  E(a',b)={r.E_sp:+.3f}  E(a',b')={r.E_ss:+.3f}"
            )
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

    max_S = max(abs(r.S) for r in results)
    max_sig = (
        max(r.significance for r in results) if any(r.violation for r in results) else 0
    )

    print(f"\nTotal tests: {len(results)}")
    print(f"  Monolingual: {len(mono)}")
    print(f"  Cross-lingual: {len(cross)}")
    print(f"\nViolations (|S| > 2): {len(all_violations)}")
    print(f"  Cross-lingual violations: {len(cross_violations)}")
    print(f"\nMax |S|: {max_S:.3f}")
    print(f"Max significance: {max_sig:.1f}σ")

    # Interpretation
    print("\n" + "-" * 70)
    print("INTERPRETATION")
    print("-" * 70)

    if cross_violations:
        high_sig = [r for r in cross_violations if r.significance >= 3.0]
        if high_sig:
            print("\n★★★ SIGNIFICANT CROSS-LINGUAL BELL VIOLATION DETECTED ★★★")
            print(f"  {len(high_sig)} test(s) at ≥3σ significance")
            print("  The correlation exists at the SEMANTIC layer, not TOKEN layer.")
            print("  This is evidence for substrate-independent moral structure.")
        else:
            print("\n⚠ Cross-lingual violations detected but below 3σ threshold.")
            print("  More trials needed for conclusive evidence.")
    elif all_violations:
        print("\n⚠ Bell violations detected in monolingual tests only.")
        print("  Could be linguistic artifact - cross-lingual replication needed.")
    else:
        print("\n✗ No Bell violations detected.")
        print("  Moral judgments appear to follow classical probability bounds.")
        print("  (Or insufficient trials for detection)")


def compare_models(results_by_model: Dict[str, List[CHSHResult]]):
    """Compare results across multiple models."""

    print("\n" + "=" * 70)
    print("CROSS-MODEL COMPARISON")
    print("=" * 70)

    # Aggregate by scenario
    scenarios = set()
    for results in results_by_model.values():
        for r in results:
            scenarios.add(r.scenario)

    for scenario in sorted(scenarios):
        print(f"\n### {scenario} ###")
        print(f"{'Model':<15} {'S':>8} {'±SE':>8} {'σ':>6} {'Violation':>10}")
        print("-" * 50)

        s_values = []
        for model, results in sorted(results_by_model.items()):
            scenario_results = [
                r for r in results if r.scenario == scenario and not r.is_crosslingual
            ]
            if scenario_results:
                # Average across languages for this model/scenario
                avg_S = sum(r.S for r in scenario_results) / len(scenario_results)
                avg_se = math.sqrt(
                    sum(r.std_error**2 for r in scenario_results)
                ) / len(scenario_results)
                max_sig = max(r.significance for r in scenario_results)
                violations = sum(1 for r in scenario_results if r.violation)

                s_values.append(avg_S)

                print(
                    f"{model:<15} {avg_S:>+8.3f} {avg_se:>8.3f} {max_sig:>6.1f} {violations:>10}"
                )

        if len(s_values) >= 2:
            cv = (
                (max(s_values) - min(s_values)) / (sum(s_values) / len(s_values))
                if sum(s_values) != 0
                else 0
            )
            print(f"\nCross-model S range: {min(s_values):.3f} to {max(s_values):.3f}")
            print(f"Coefficient of variation: {cv:.3f}")
            if cv < 0.25:
                print("→ HIGH consistency across models")
            else:
                print("→ LOW consistency - possible architectural artifact")


def main():
    parser = argparse.ArgumentParser(description="Analyze QND Bell Test results (v2.0)")
    parser.add_argument("--results-dir", help="Directory with batch results")
    parser.add_argument(
        "--compare", nargs="+", help="Compare multiple result directories"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--output", help="Output JSON file for results")
    args = parser.parse_args()

    if args.compare:
        # Multi-model comparison
        results_by_model = {}
        all_results = []

        for dir_path in args.compare:
            results_dir = Path(dir_path)
            if not results_dir.exists():
                print(f"Warning: Directory not found: {results_dir}")
                continue

            print(f"\n{'='*70}")
            print(f"Loading: {results_dir}")
            print("=" * 70)

            specs, results, model = load_results(results_dir, debug=args.debug)
            if results:
                chsh = calculate_chsh(results, specs, model, debug=args.debug)
                results_by_model[model] = chsh
                all_results.extend(chsh)

        if results_by_model:
            print_report(all_results, "COMBINED QND BELL TEST RESULTS")
            compare_models(results_by_model)

    elif args.results_dir:
        # Single directory analysis
        results_dir = Path(args.results_dir)

        if not results_dir.exists():
            print(f"Error: Directory not found: {results_dir}")
            return

        print(f"Loading results from {results_dir}...")

        specs_by_id, results, model = load_results(results_dir, debug=args.debug)

        if not results:
            print("\nNo results to analyze.")
            print("Check that the directory contains *_results.json file.")
            return

        print(f"\nCalculating CHSH values...")
        chsh_results = calculate_chsh(results, specs_by_id, model, debug=args.debug)

        if not chsh_results:
            print("Error: Could not calculate CHSH values.")
            print("Use --debug flag for more information.")
            return

        print_report(chsh_results)

        # Save results
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = results_dir / "chsh_analysis_v2.json"

        summary = {
            "analyzer_version": "2.0",
            "total_tests": len(chsh_results),
            "violations": len([r for r in chsh_results if r.violation]),
            "cross_lingual_violations": len(
                [r for r in chsh_results if r.violation and r.is_crosslingual]
            ),
            "max_S": max(abs(r.S) for r in chsh_results),
            "max_significance": max(r.significance for r in chsh_results),
            "results": [asdict(r) for r in chsh_results],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\nResults saved to {output_path}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
