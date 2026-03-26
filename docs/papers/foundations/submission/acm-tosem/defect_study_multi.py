"""Run structural fuzzing on multiple NASA MDP datasets for TOSEM replication.

Adds JM1 (10,885 modules) and PC1 (1,109 modules) alongside KC1.
"""

from __future__ import annotations

import itertools
import json
from collections import defaultdict

import numpy as np
from sklearn.datasets import fetch_openml
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, roc_auc_score, accuracy_score
from sklearn.model_selection import StratifiedKFold

# ---------------------------------------------------------------------------
# Feature group definitions per dataset
# ---------------------------------------------------------------------------

# KC1, JM1, PC1 all share the same NASA MDP feature set
GROUPS = {
    "g1_Size": ["loc", "lOCode", "lOComment", "lOBlank", "locCodeAndComment"],
    "g2_Complexity": ["v(g)", "ev(g)", "iv(g)", "branchCount"],
    "g3_Halstead": ["n", "v", "l", "d", "i", "e", "b", "t"],
    "g4_Operators": ["uniq_Op", "uniq_Opnd", "total_Op", "total_Opnd"],
}
GROUP_NAMES = list(GROUPS.keys())
GROUP_SHORT = ["Size", "Complexity", "Halstead", "Operators"]


def get_group_features(group_indices):
    features = []
    for gi in group_indices:
        features.extend(GROUPS[GROUP_NAMES[gi]])
    return features


def load_dataset(name):
    data = fetch_openml(name=name, version=1, as_frame=True, parser="auto")
    X = data.data
    # Handle different target encodings
    target = data.target
    if target.dtype == object or hasattr(target, 'cat'):
        unique_vals = sorted(target.unique())
        # Map to binary: last value is defective
        y = (target == unique_vals[-1]).astype(int).values
    else:
        y = target.astype(int).values

    # Check which features are available
    available = [c for c in X.columns if c in sum(GROUPS.values(), [])]
    missing = [c for c in sum(GROUPS.values(), []) if c not in X.columns]
    if missing:
        print(f"  Warning: missing features: {missing}")

    return X, y, available


def evaluate_rf(X, y, feature_cols, seed=42, n_folds=5):
    if not feature_cols:
        majority = int(np.bincount(y).argmax())
        preds = np.full(len(y), majority)
        return {"f1": f1_score(y, preds, zero_division=0), "auc": 0.5,
                "accuracy": accuracy_score(y, preds)}

    Xf = X[feature_cols].values
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    metrics = defaultdict(list)
    for train_idx, test_idx in skf.split(Xf, y):
        rf = RandomForestClassifier(n_estimators=100, max_depth=10,
                                     random_state=seed, n_jobs=-1)
        rf.fit(Xf[train_idx], y[train_idx])
        preds = rf.predict(Xf[test_idx])
        probs = rf.predict_proba(Xf[test_idx])[:, 1]
        metrics["f1"].append(f1_score(y[test_idx], preds, zero_division=0))
        metrics["auc"].append(roc_auc_score(y[test_idx], probs))
        metrics["accuracy"].append(accuracy_score(y[test_idx], preds))
    return {k: float(np.mean(v)) for k, v in metrics.items()}


def run_campaign(name, X, y):
    print(f"\n{'='*60}")
    print(f"  {name}: {len(y)} modules, {y.sum()} defective ({100*y.mean():.1f}%)")
    print(f"{'='*60}")

    # 1. Enumerate all subsets
    best_at_k = {}
    for k in range(5):
        for combo in itertools.combinations(range(4), k):
            if k == 0:
                features = []
            else:
                features = get_group_features(list(combo))
            m = evaluate_rf(X, y, features)
            if k not in best_at_k or m["f1"] > best_at_k[k]["f1"]:
                best_at_k[k] = {
                    "groups": [GROUP_SHORT[g] for g in combo] if k > 0 else ["(null)"],
                    "f1": m["f1"], "auc": m["auc"], "acc": m["accuracy"],
                    "group_idx": list(combo) if k > 0 else [],
                }

    print("\n  Pareto frontier:")
    print(f"  {'k':>3}  {'Subset':<35}  {'F1':>6}  {'AUC':>6}")
    for k in sorted(best_at_k):
        b = best_at_k[k]
        print(f"  {k:>3}  {', '.join(b['groups']):<35}  {b['f1']:.3f}  {b['auc']:.3f}")

    # 2. Sensitivity (from full model)
    all_feats = get_group_features(list(range(4)))
    base = evaluate_rf(X, y, all_feats)
    print(f"\n  Sensitivity (base F1={base['f1']:.3f}):")
    deltas = []
    for gi in range(4):
        ablated = [g for g in range(4) if g != gi]
        abl_feats = get_group_features(ablated)
        abl = evaluate_rf(X, y, abl_feats)
        d = base["f1"] - abl["f1"]
        deltas.append(d)
        print(f"    {GROUP_SHORT[gi]:<15}  delta={d:+.4f}")

    # 3. MRI (50 perturbations for speed)
    rng = np.random.RandomState(42)
    omegas = []
    Xf = X[all_feats].copy()
    for i in range(50):
        X_pert = Xf.copy()
        for feat in all_feats:
            noise = np.exp(rng.normal(0, 0.5, size=len(X_pert)))
            X_pert[feat] = X_pert[feat] * noise
        pm = evaluate_rf(X_pert, y, all_feats, seed=42+i, n_folds=3)
        omegas.append(abs(pm["f1"] - base["f1"]))

    omegas = np.array(omegas)
    mri = 0.5 * np.mean(omegas) + 0.3 * np.percentile(omegas, 75) + 0.2 * np.percentile(omegas, 95)
    mri_rel = mri / max(base["f1"], 0.01)  # Relative MRI
    print(f"\n  MRI = {mri:.4f} (relative: {mri_rel:.3f})")
    print(f"    mean(w)={np.mean(omegas):.4f}  P75={np.percentile(omegas,75):.4f}  P95={np.percentile(omegas,95):.4f}")

    # 4. Compositional (from Size)
    print(f"\n  Compositional (from Size):")
    current = [0]
    remaining = [1, 2, 3]
    m = evaluate_rf(X, y, get_group_features(current))
    print(f"    1. Size: F1={m['f1']:.3f}")
    step = 2
    while remaining:
        best_f1, best_g = -1, None
        for gi in remaining:
            trial = current + [gi]
            tm = evaluate_rf(X, y, get_group_features(trial))
            if tm["f1"] > best_f1:
                best_f1 = tm["f1"]
                best_g = gi
        current.append(best_g)
        remaining.remove(best_g)
        print(f"    {step}. +{GROUP_SHORT[best_g]}: F1={best_f1:.3f}")
        step += 1

    return {
        "name": name,
        "n": len(y),
        "defect_rate": float(y.mean()),
        "pareto": {str(k): v for k, v in best_at_k.items()},
        "sensitivity": {GROUP_SHORT[i]: float(deltas[i]) for i in range(4)},
        "mri": float(mri),
        "mri_rel": float(mri_rel),
        "base_f1": float(base["f1"]),
    }


def main():
    datasets = ["kc1", "jm1", "pc1"]
    all_results = {}

    for ds in datasets:
        print(f"\nLoading {ds}...")
        try:
            X, y, avail = load_dataset(ds)
            result = run_campaign(ds.upper(), X, y)
            all_results[ds] = result
        except Exception as ex:
            print(f"  FAILED: {ex}")

    # Cross-dataset comparison
    print(f"\n{'='*60}")
    print("CROSS-DATASET COMPARISON")
    print(f"{'='*60}")
    print(f"  {'Dataset':<8}  {'N':>6}  {'Def%':>5}  {'F1':>6}  {'MRI':>6}  {'MRI_rel':>8}  {'Top sens.':<15}")
    for ds, r in all_results.items():
        top_s = max(r["sensitivity"], key=r["sensitivity"].get)
        print(f"  {r['name']:<8}  {r['n']:>6}  {100*r['defect_rate']:>4.1f}%  "
              f"{r['base_f1']:>6.3f}  {r['mri']:>6.4f}  {r['mri_rel']:>8.3f}  {top_s}")

    with open("defect_multi_results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print("\nResults saved to defect_multi_results.json")


if __name__ == "__main__":
    main()
