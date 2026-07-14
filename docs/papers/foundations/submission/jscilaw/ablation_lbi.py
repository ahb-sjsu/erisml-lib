"""LBI robustness ablation (responds to JSciLaw review points 1,2,3,5,7,8).

Recomputes LBI(race) at k=20 across:
  (A) legitimate-feature sets: minimal / paper-6 / drop-contested-proxies / +sex-control
  (B) score representations: raw decile / 3-category (low-med-high) / binary high-risk

Purpose: show whether the ~1.05 case-level signal is robust to the choice of legitimate
features (the reviewer's central objection) and whether it survives at the legally-salient
decision unit (category), rather than only the raw decile. Same Mahalanobis k-NN matched-pair
estimator as lbi_compas_analysis.py.
"""
import pathlib

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

rng = np.random.default_rng(20260611)
ROOT = pathlib.Path(__file__).parent
df_raw = pd.read_csv(ROOT / "data" / "compas-scores-two-years.csv")
df = df_raw[
    (df_raw["days_b_screening_arrest"].between(-30, 30))
    & (df_raw["is_recid"] != -1)
    & (df_raw["c_charge_degree"] != "O")
    & (df_raw["score_text"] != "N/A")
].copy().reset_index(drop=True)
df = df[df["race"].isin(["African-American", "Caucasian"])].copy().reset_index(drop=True)
df["c_charge_F"] = (df["c_charge_degree"] == "F").astype(int)
df["male"] = (df["sex"] == "Male").astype(int)
print(f"n = {len(df)}")

group_race = (df["race"] == "African-American").astype(int).values


def compute_lbi_k(X, scores, group, k=20, sigma_inv=None, n_boot=1000):
    if sigma_inv is not None:
        w, V = np.linalg.eigh(sigma_inv)
        L = V @ np.diag(np.sqrt(np.clip(w, 1e-12, None)))
        Xm = X @ L
    else:
        Xm = X
    diffs, sames = [], []
    for i in range(len(Xm)):
        own = group[i]
        for mask, store in ((group != own, diffs), ((group == own) & (np.arange(len(group)) != i), sames)):
            ci = np.where(mask)[0]
            if len(ci) < k:
                continue
            d = np.linalg.norm(Xm[ci] - Xm[i], axis=1)
            nn = ci[np.argsort(d)[:k]]
            store.append(np.abs(scores[nn] - scores[i]).mean())
    diff = np.array(diffs); same = np.array(sames)
    m = min(len(diff), len(same)); diff, same = diff[:m], same[:m]
    lbi = diff.mean() / same.mean()
    bl = [diff[b].mean() / same[b].mean() for b in (rng.integers(0, m, m) for _ in range(n_boot))]
    lo, hi = np.nanpercentile(bl, [2.5, 97.5])
    return lbi, lo, hi, m


FEATSETS = {
    "minimal [age,priors]": ["age", "priors_count"],
    "paper-6": ["age", "priors_count", "juv_fel_count", "juv_misd_count", "juv_other_count", "c_charge_F"],
    "drop-juvenile (contested proxies)": ["age", "priors_count", "c_charge_F"],
    "paper-6 + sex control": ["age", "priors_count", "juv_fel_count", "juv_misd_count", "juv_other_count", "c_charge_F", "male"],
}
decile = df["decile_score"].values.astype(float)
cat3 = np.select([df["decile_score"] <= 4, df["decile_score"] <= 7], [0.0, 1.0], default=2.0)  # low/med/high
binhi = (df["decile_score"] >= 5).astype(float).values

print("\n=== (A) feature-set robustness — LBI(race) at k=20, score = decile ===")
print(f"{'feature set':<38}{'LBI':>7}{'95% CI':>18}{'n':>7}")
for name, feats in FEATSETS.items():
    Xz = StandardScaler().fit_transform(df[feats].values.astype(float))
    Sig = np.cov(Xz, rowvar=False) + 1e-6 * np.eye(len(feats))
    lbi, lo, hi, n = compute_lbi_k(Xz, decile, group_race, sigma_inv=np.linalg.inv(Sig))
    print(f"{name:<38}{lbi:>7.3f}   [{lo:.3f}, {hi:.3f}]{n:>7}")

print("\n=== (B) score representation — LBI(race) at k=20, features = paper-6 ===")
feats = FEATSETS["paper-6"]
Xz = StandardScaler().fit_transform(df[feats].values.astype(float))
Sinv = np.linalg.inv(np.cov(Xz, rowvar=False) + 1e-6 * np.eye(len(feats)))
for name, sc in (("raw decile (1-10)", decile), ("3-category (low/med/high)", cat3), ("binary high-risk (>=5)", binhi)):
    lbi, lo, hi, n = compute_lbi_k(Xz, sc, group_race, sigma_inv=Sinv)
    print(f"  {name:<28} LBI={lbi:.3f}  [{lo:.3f}, {hi:.3f}]")
print("\n(decile CI that excludes 1.0 across feature sets => the case-level signal is not an artifact\n of the paper's particular 6-feature choice; category/binary => survival at the decision unit.)")
