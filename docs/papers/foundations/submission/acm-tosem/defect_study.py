"""Structural fuzzing case study on real software defect prediction data.

Uses the KC1 dataset from NASA/PROMISE repository (via OpenML).
KC1: 2,109 modules from a storage management system for receiving/processing
ground data, with 21 static code metrics and binary defect labels.

Feature groups:
  g1 (Size):       loc, lOCode, lOComment, lOBlank, locCodeAndComment
  g2 (Complexity):  v(g), ev(g), iv(g), branchCount
  g3 (Halstead):   n, v, l, d, i, e, b, t
  g4 (Operators):  uniq_Op, uniq_Opnd, total_Op, total_Opnd
"""

from __future__ import annotations

import itertools
import json
from collections import defaultdict

import numpy as np
from sklearn.datasets import fetch_openml
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold

# ---------------------------------------------------------------------------
# Data loading and feature groups
# ---------------------------------------------------------------------------

GROUPS = {
    "g1_Size": ["loc", "lOCode", "lOComment", "lOBlank", "locCodeAndComment"],
    "g2_Complexity": ["v(g)", "ev(g)", "iv(g)", "branchCount"],
    "g3_Halstead": ["n", "v", "l", "d", "i", "e", "b", "t"],
    "g4_Operators": ["uniq_Op", "uniq_Opnd", "total_Op", "total_Opnd"],
}

GROUP_NAMES = list(GROUPS.keys())
GROUP_SHORT = ["Size", "Complexity", "Halstead", "Operators"]


def load_data():
    data = fetch_openml(name="kc1", version=1, as_frame=True, parser="auto")
    X = data.data
    y = (data.target == "true").astype(int).values
    return X, y


def get_group_features(group_indices: list[int]) -> list[str]:
    features = []
    for gi in group_indices:
        features.extend(GROUPS[GROUP_NAMES[gi]])
    return features


# ---------------------------------------------------------------------------
# Evaluation helper — stratified 5-fold CV
# ---------------------------------------------------------------------------


def evaluate_rf(X, y, feature_cols, seed=42, n_folds=5):
    """Train RF on given features, return mean metrics over 5-fold CV."""
    if not feature_cols:
        # No features — predict majority class
        majority = int(np.bincount(y).argmax())
        preds = np.full(len(y), majority)
        return {
            "accuracy": accuracy_score(y, preds),
            "precision": precision_score(y, preds, zero_division=0),
            "recall": recall_score(y, preds, zero_division=0),
            "f1": f1_score(y, preds, zero_division=0),
            "auc": 0.5,
        }

    Xf = X[feature_cols].values
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    metrics = defaultdict(list)

    for train_idx, test_idx in skf.split(Xf, y):
        rf = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=seed, n_jobs=-1
        )
        rf.fit(Xf[train_idx], y[train_idx])
        preds = rf.predict(Xf[test_idx])
        probs = rf.predict_proba(Xf[test_idx])[:, 1]

        metrics["accuracy"].append(accuracy_score(y[test_idx], preds))
        metrics["precision"].append(precision_score(y[test_idx], preds, zero_division=0))
        metrics["recall"].append(recall_score(y[test_idx], preds, zero_division=0))
        metrics["f1"].append(f1_score(y[test_idx], preds, zero_division=0))
        metrics["auc"].append(roc_auc_score(y[test_idx], probs))

    return {k: float(np.mean(v)) for k, v in metrics.items()}


# ---------------------------------------------------------------------------
# 1. Dimension enumeration + Pareto frontier
# ---------------------------------------------------------------------------


def enumerate_subsets(X, y):
    """Evaluate all non-empty subsets of 4 feature groups."""
    results = []
    n_groups = len(GROUP_NAMES)

    for k in range(n_groups + 1):
        for combo in itertools.combinations(range(n_groups), k):
            if k == 0:
                # Null model
                features = []
                groups_used = []
            else:
                groups_used = list(combo)
                features = get_group_features(groups_used)

            metrics = evaluate_rf(X, y, features)
            results.append({
                "groups": groups_used,
                "group_names": [GROUP_SHORT[g] for g in groups_used],
                "n_groups": k,
                "features": features,
                "n_features": len(features),
                **metrics,
            })

    # Sort by F1 descending
    results.sort(key=lambda r: r["f1"], reverse=True)

    # Mark Pareto-optimal (best F1 at each group count)
    best_at_k = {}
    for r in results:
        k = r["n_groups"]
        if k not in best_at_k or r["f1"] > best_at_k[k]["f1"]:
            best_at_k[k] = r

    pareto = []
    for k in sorted(best_at_k.keys()):
        entry = best_at_k[k].copy()
        entry["pareto_optimal"] = True
        pareto.append(entry)

    return results, pareto


# ---------------------------------------------------------------------------
# 2. Sensitivity profiling
# ---------------------------------------------------------------------------


def sensitivity_profile(X, y, base_groups=None):
    """Ablate each group and measure F1 drop."""
    if base_groups is None:
        base_groups = list(range(len(GROUP_NAMES)))

    all_features = get_group_features(base_groups)
    base_metrics = evaluate_rf(X, y, all_features)

    sensitivities = []
    for gi in range(len(GROUP_NAMES)):
        if gi not in base_groups:
            sensitivities.append({
                "group": gi,
                "group_name": GROUP_SHORT[gi],
                "f1_with": base_metrics["f1"],
                "f1_without": base_metrics["f1"],
                "delta_f1": 0.0,
            })
            continue

        ablated = [g for g in base_groups if g != gi]
        ablated_features = get_group_features(ablated)
        ablated_metrics = evaluate_rf(X, y, ablated_features)

        sensitivities.append({
            "group": gi,
            "group_name": GROUP_SHORT[gi],
            "f1_with": base_metrics["f1"],
            "f1_without": ablated_metrics["f1"],
            "delta_f1": base_metrics["f1"] - ablated_metrics["f1"],
            "acc_with": base_metrics["accuracy"],
            "acc_without": ablated_metrics["accuracy"],
            "delta_acc": base_metrics["accuracy"] - ablated_metrics["accuracy"],
        })

    # Rank by delta_f1
    sensitivities.sort(key=lambda s: s["delta_f1"], reverse=True)
    for rank, s in enumerate(sensitivities, 1):
        s["rank"] = rank

    return sensitivities


# ---------------------------------------------------------------------------
# 3. Model Robustness Index (MRI)
# ---------------------------------------------------------------------------


def compute_mri(X, y, base_groups=None, n_perturbations=100, scale=0.5, seed=42):
    """Compute MRI by perturbing feature values and retraining."""
    if base_groups is None:
        base_groups = list(range(len(GROUP_NAMES)))

    all_features = get_group_features(base_groups)
    base_metrics = evaluate_rf(X, y, all_features)
    base_f1 = base_metrics["f1"]

    rng = np.random.RandomState(seed)
    omegas = []

    Xf = X[all_features].copy()

    for i in range(n_perturbations):
        # Perturb each feature by multiplicative log-normal noise
        X_pert = Xf.copy()
        for feat in all_features:
            noise = np.exp(rng.normal(0, scale, size=len(X_pert)))
            X_pert[feat] = X_pert[feat] * noise

        # Evaluate with perturbed features (3-fold for speed)
        pert_metrics = evaluate_rf(X_pert, y, all_features, seed=seed + i, n_folds=3)
        omega = abs(pert_metrics["f1"] - base_f1)
        omegas.append(omega)

    omegas = np.array(omegas)
    mean_omega = float(np.mean(omegas))
    p75 = float(np.percentile(omegas, 75))
    p95 = float(np.percentile(omegas, 95))
    mri = 0.5 * mean_omega + 0.3 * p75 + 0.2 * p95

    # Distribution bins
    bins = [0, 0.02, 0.05, 0.10, 0.15, 0.20, 1.0]
    hist, _ = np.histogram(omegas, bins=bins)
    hist_pct = (hist / len(omegas) * 100).tolist()

    return {
        "mri": float(mri),
        "mean_omega": mean_omega,
        "p75": p75,
        "p95": p95,
        "n_perturbations": n_perturbations,
        "scale": scale,
        "base_f1": base_f1,
        "worst_case_f1": float(base_f1 - np.max(omegas)),
        "omegas": omegas.tolist(),
        "hist_bins": bins,
        "hist_pct": hist_pct,
    }


# ---------------------------------------------------------------------------
# 4. Adversarial threshold search
# ---------------------------------------------------------------------------


def adversarial_threshold(X, y, base_groups=None, threshold=0.02, seed=42):
    """Find minimal noise scale on each group that degrades F1 by > threshold."""
    if base_groups is None:
        base_groups = list(range(len(GROUP_NAMES)))

    all_features = get_group_features(base_groups)
    base_metrics = evaluate_rf(X, y, all_features)
    base_f1 = base_metrics["f1"]

    results = []
    scales_to_test = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0]

    for gi in base_groups:
        group_features = GROUPS[GROUP_NAMES[gi]]
        found_threshold = None

        for s in scales_to_test:
            rng = np.random.RandomState(seed)
            X_pert = X[all_features].copy()
            for feat in group_features:
                noise = np.exp(rng.normal(0, s, size=len(X_pert)))
                X_pert[feat] = X_pert[feat] * noise

            pert_metrics = evaluate_rf(X_pert, y, all_features, n_folds=3)
            delta = base_f1 - pert_metrics["f1"]

            if delta > threshold:
                found_threshold = s
                break

        results.append({
            "group": gi,
            "group_name": GROUP_SHORT[gi],
            "threshold_scale": found_threshold if found_threshold else "> 5.0",
            "base_f1": base_f1,
        })

    return results


# ---------------------------------------------------------------------------
# 5. Compositional test
# ---------------------------------------------------------------------------


def compositional_test(X, y, start_group=0):
    """Greedily add groups starting from start_group."""
    remaining = list(range(len(GROUP_NAMES)))
    remaining.remove(start_group)

    current = [start_group]
    features = get_group_features(current)
    metrics = evaluate_rf(X, y, features)

    steps = [{
        "step": 1,
        "added": GROUP_SHORT[start_group],
        "groups": [GROUP_SHORT[g] for g in current],
        "f1": metrics["f1"],
        "accuracy": metrics["accuracy"],
        "auc": metrics["auc"],
    }]

    while remaining:
        best_f1 = -1
        best_group = None

        for gi in remaining:
            trial = current + [gi]
            trial_features = get_group_features(trial)
            trial_metrics = evaluate_rf(X, y, trial_features)
            if trial_metrics["f1"] > best_f1:
                best_f1 = trial_metrics["f1"]
                best_group = gi

        current.append(best_group)
        remaining.remove(best_group)
        features = get_group_features(current)
        metrics = evaluate_rf(X, y, features)

        steps.append({
            "step": len(current),
            "added": GROUP_SHORT[best_group],
            "groups": [GROUP_SHORT[g] for g in current],
            "f1": metrics["f1"],
            "accuracy": metrics["accuracy"],
            "auc": metrics["auc"],
        })

    return steps


# ---------------------------------------------------------------------------
# 6. Forward / backward selection (baselines)
# ---------------------------------------------------------------------------


def forward_selection(X, y):
    """Standard forward feature group selection."""
    remaining = list(range(len(GROUP_NAMES)))
    current = []
    steps = []

    while remaining:
        best_f1 = -1
        best_group = None

        for gi in remaining:
            trial = current + [gi]
            trial_features = get_group_features(trial)
            trial_metrics = evaluate_rf(X, y, trial_features)
            if trial_metrics["f1"] > best_f1:
                best_f1 = trial_metrics["f1"]
                best_group = gi

        current.append(best_group)
        remaining.remove(best_group)
        steps.append({
            "step": len(current),
            "added": GROUP_SHORT[best_group],
            "f1": best_f1,
        })

    return steps


def backward_elimination(X, y):
    """Standard backward feature group elimination."""
    current = list(range(len(GROUP_NAMES)))
    all_features = get_group_features(current)
    base_metrics = evaluate_rf(X, y, all_features)
    steps = [{
        "step": 0,
        "removed": "none",
        "remaining": [GROUP_SHORT[g] for g in current],
        "f1": base_metrics["f1"],
    }]

    while len(current) > 1:
        best_f1 = -1
        best_remove = None

        for gi in current:
            trial = [g for g in current if g != gi]
            trial_features = get_group_features(trial)
            trial_metrics = evaluate_rf(X, y, trial_features)
            if trial_metrics["f1"] > best_f1:
                best_f1 = trial_metrics["f1"]
                best_remove = gi

        current.remove(best_remove)
        steps.append({
            "step": len(steps),
            "removed": GROUP_SHORT[best_remove],
            "remaining": [GROUP_SHORT[g] for g in current],
            "f1": best_f1,
        })

    return steps


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("=" * 70)
    print("STRUCTURAL FUZZING — KC1 DEFECT PREDICTION CASE STUDY")
    print("=" * 70)

    print("\nLoading KC1 dataset...")
    X, y = load_data()
    print(f"  Instances: {len(y)}")
    print(f"  Defective: {y.sum()} ({100*y.mean():.1f}%)")
    print(f"  Features:  {X.shape[1]}")
    print(f"  Groups:    {len(GROUP_NAMES)}")
    for gn, feats in GROUPS.items():
        print(f"    {gn}: {feats}")

    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("1. DIMENSION ENUMERATION + PARETO FRONTIER")
    print("=" * 70)
    all_results, pareto = enumerate_subsets(X, y)
    print("\nPareto frontier:")
    print(f"  {'Groups':>6}  {'Best Subset':<40}  {'F1':>6}  {'AUC':>6}  {'Acc':>6}")
    for p in pareto:
        print(
            f"  {p['n_groups']:>6}  {', '.join(p['group_names']) or '(null)':<40}"
            f"  {p['f1']:>6.3f}  {p['auc']:>6.3f}  {p['accuracy']:>6.3f}"
        )

    # Find best model
    best = max(all_results, key=lambda r: r["f1"])
    print(f"\nBest overall: {best['group_names']} (k={best['n_groups']}, F1={best['f1']:.4f})")

    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("2. SENSITIVITY PROFILING")
    print("=" * 70)
    sens = sensitivity_profile(X, y)
    print(f"\n  {'Group':<15}  {'F1 with':>8}  {'F1 without':>11}  {'Delta F1':>9}  {'Rank':>5}")
    for s in sens:
        print(
            f"  {s['group_name']:<15}  {s['f1_with']:>8.4f}  {s['f1_without']:>11.4f}"
            f"  {s['delta_f1']:>+9.4f}  {s['rank']:>5}"
        )

    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("3. MODEL ROBUSTNESS INDEX (MRI)")
    print("=" * 70)
    print("  Computing MRI (300 perturbations)...")
    mri_result = compute_mri(X, y)
    print(f"  Base F1:     {mri_result['base_f1']:.4f}")
    print(f"  mean(w):     {mri_result['mean_omega']:.4f}")
    print(f"  P75(w):      {mri_result['p75']:.4f}")
    print(f"  P95(w):      {mri_result['p95']:.4f}")
    print(f"  MRI:         {mri_result['mri']:.4f}")
    print(f"  Worst-case:  {mri_result['worst_case_f1']:.4f}")
    print(f"\n  Distribution of w:")
    bins = mri_result["hist_bins"]
    pcts = mri_result["hist_pct"]
    for i in range(len(pcts)):
        print(f"    [{bins[i]:.2f}, {bins[i+1]:.2f}): {pcts[i]:5.1f}%")

    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("4. ADVERSARIAL THRESHOLD SEARCH")
    print("=" * 70)
    adv = adversarial_threshold(X, y)
    print(f"\n  {'Group':<15}  {'Threshold Scale':>16}")
    for a in adv:
        print(f"  {a['group_name']:<15}  {str(a['threshold_scale']):>16}")

    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("5. COMPOSITIONAL TEST (starting from Size)")
    print("=" * 70)
    comp = compositional_test(X, y, start_group=0)  # Start from Size
    print(f"\n  {'Step':>4}  {'Added':<15}  {'F1':>6}  {'AUC':>6}  {'Acc':>6}")
    for c in comp:
        print(
            f"  {c['step']:>4}  {c['added']:<15}  {c['f1']:>6.3f}"
            f"  {c['auc']:>6.3f}  {c['accuracy']:>6.3f}"
        )

    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("6. BASELINE COMPARISONS")
    print("=" * 70)

    print("\nForward selection:")
    fwd = forward_selection(X, y)
    for f in fwd:
        print(f"  Step {f['step']}: +{f['added']:<15}  F1={f['f1']:.4f}")

    print("\nBackward elimination:")
    bwd = backward_elimination(X, y)
    for b in bwd:
        print(
            f"  Step {b['step']}: -{b['removed']:<15}"
            f"  remaining={b['remaining']}  F1={b['f1']:.4f}"
        )

    # -----------------------------------------------------------------------
    # Save all results
    results = {
        "dataset": "KC1",
        "n_instances": len(y),
        "n_defective": int(y.sum()),
        "defect_rate": float(y.mean()),
        "pareto": pareto,
        "sensitivity": sens,
        "mri": {k: v for k, v in mri_result.items() if k != "omegas"},
        "adversarial": adv,
        "compositional": comp,
        "forward_selection": fwd,
        "backward_elimination": bwd,
    }

    out_path = "defect_study_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
