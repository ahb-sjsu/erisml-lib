"""LBI revision-2 analysis — responds to JSciLaw editorial review (2026-07).

Addresses, computationally:
  R1  distance diagnostics (same- vs cross-race neighbor distances), balance/common support,
      caliper exclusion, distance-matched specification, exact matching on felony indicator
  R2  permutation test at full n with 1000 permutations; conditional randomization test (CRT)
      preserving P(race|X); propensity-stratified permutation; bootstrap that RE-FORMS
      neighborhoods inside every replicate
  R3  semi-synthetic ground-truth validation: (1) race-blind score, (2) explicit race
      coefficient, (3) strong race proxy, (4) omitted legitimate predictor; FPR + power for
      plain permutation vs CRT; regression-coefficient and Dwork-consistency baselines
  R4  COMPAS category cutoffs: binary >=5 (ProPublica's medium-or-high) and >=8 (high);
      raw cross/same disagreement rates (numerator and denominator of the ratio)
  R5  matching-method robustness: Euclidean, robust Mahalanobis (MinCovDet), Gower,
      log1p and rank transforms, coarsened-exact matching, fixed-radius calipers
  R7b sex result across k with multiscale permutation; k-curve as the primary object;
      global (multiscale max-z) permutation test rather than k=20 alone
  R8  focal-group split (Black focal / White focal) + group-balanced LBI; distribution of
      per-defendant cross-minus-same gaps; neighbor-reuse and tie statistics

Run:  python revision2_analysis.py   (expects compas-scores-two-years.csv alongside)
Outputs -> ./outputs/revision2_results.json, revision2_report.txt, figures/*.pdf
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd
from numba import njit, prange
from scipy.spatial.distance import cdist
from scipy.stats import rankdata
from sklearn.covariance import MinCovDet
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler

SEED = 20260724
rng = np.random.default_rng(SEED)
ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "outputs"
FIG = ROOT / "figures"
OUT.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

KS = np.array([1, 5, 10, 20, 50, 100], dtype=np.int64)
KMAX = 100
K20 = int(np.where(KS == 20)[0][0])
N_PERM = 1000
N_BOOT = 1000

# ----------------------------------------------------------------------------- data
df_raw = pd.read_csv(ROOT / "compas-scores-two-years.csv")
df = df_raw[
    (df_raw["days_b_screening_arrest"].between(-30, 30))
    & (df_raw["is_recid"] != -1)
    & (df_raw["c_charge_degree"] != "O")
    & (df_raw["score_text"] != "N/A")
].copy()
df = df[df["race"].isin(["African-American", "Caucasian"])].copy().reset_index(drop=True)
df["c_charge_F"] = (df["c_charge_degree"] == "F").astype(int)
df["male"] = (df["sex"] == "Male").astype(int)
n = len(df)
print(f"n = {n}", flush=True)

FEATS6 = ["age", "priors_count", "juv_fel_count", "juv_misd_count", "juv_other_count", "c_charge_F"]
X_raw = df[FEATS6].values.astype(np.float64)
assert not np.isnan(X_raw).any(), "missing values in features"

g_race = (df["race"] == "African-American").astype(np.int8).values
g_sex = df["male"].values.astype(np.int8)
decile = df["decile_score"].values.astype(np.float64)
cat3 = np.select([df["decile_score"] <= 4, df["decile_score"] <= 7], [0.0, 1.0], default=2.0)
bin5 = (df["decile_score"] >= 5).values.astype(np.float64)   # ProPublica: medium-or-high
bin8 = (df["decile_score"] >= 8).values.astype(np.float64)   # high category only


def whiten(X, robust=False):
    """Standardize then whiten so Euclidean distance = Mahalanobis distance."""
    Xz = StandardScaler().fit_transform(X)
    if robust:
        S = MinCovDet(random_state=SEED).fit(Xz).covariance_
    else:
        S = np.cov(Xz, rowvar=False)
    S = S + 1e-6 * np.eye(S.shape[1])
    w, V = np.linalg.eigh(np.linalg.inv(S))
    return Xz, (Xz @ (V @ np.diag(np.sqrt(np.clip(w, 1e-12, None))))).astype(np.float64)


def dist_sort(Xm):
    D = cdist(Xm, Xm).astype(np.float32)
    SORT = np.argsort(D, axis=1, kind="stable").astype(np.int32)
    return D, SORT


Xz6, Xm6 = whiten(X_raw)
D6, SORT6 = dist_sort(Xm6)
cond_number = float(np.linalg.cond(np.cov(Xz6, rowvar=False)))

# ----------------------------------------------------------------------------- kernels
@njit(parallel=True)
def walk_all(SORT, D, labels, stratum, use_stratum, scores, ks, kmax):
    """Per-focal mean |score gap| and mean distance to k nearest same/cross neighbors."""
    n = SORT.shape[0]
    nk = len(ks)
    sg = np.full((n, nk), np.nan)
    cg = np.full((n, nk), np.nan)
    sd = np.full((n, nk), np.nan)
    cd = np.full((n, nk), np.nan)
    for i in prange(n):
        ss = 0.0; ssd = 0.0; sc = 0
        cs = 0.0; csd = 0.0; cc = 0
        kis = 0; kic = 0
        for idx in range(SORT.shape[1]):
            j = SORT[i, idx]
            if j == i:
                continue
            if use_stratum and stratum[j] != stratum[i]:
                continue
            gap = abs(scores[j] - scores[i])
            dij = D[i, j]
            if labels[j] == labels[i]:
                if sc < kmax:
                    ss += gap; ssd += dij; sc += 1
                    while kis < nk and sc == ks[kis]:
                        sg[i, kis] = ss / sc; sd[i, kis] = ssd / sc; kis += 1
            else:
                if cc < kmax:
                    cs += gap; csd += dij; cc += 1
                    while kic < nk and cc == ks[kic]:
                        cg[i, kic] = cs / cc; cd[i, kic] = csd / cc; kic += 1
            if sc >= kmax and cc >= kmax:
                break
    return sg, cg, sd, cd


@njit(parallel=True)
def neighbor_idx_k(SORT, labels, k):
    """Indices of the k nearest same- and cross-group neighbors of each focal."""
    n = SORT.shape[0]
    same = np.full((n, k), -1, dtype=np.int32)
    cross = np.full((n, k), -1, dtype=np.int32)
    for i in prange(n):
        sc = 0; cc = 0
        for idx in range(SORT.shape[1]):
            j = SORT[i, idx]
            if j == i:
                continue
            if labels[j] == labels[i]:
                if sc < k:
                    same[i, sc] = j; sc += 1
            else:
                if cc < k:
                    cross[i, cc] = j; cc += 1
            if sc >= k and cc >= k:
                break
    return same, cross


@njit(parallel=True)
def perm_lbi(SORT, labels_mat, scores, ks, kmax):
    """LBI_k for each row of labels_mat (P x n). Returns (P x nk)."""
    P = labels_mat.shape[0]
    n = SORT.shape[0]
    nk = len(ks)
    out = np.empty((P, nk))
    for p in prange(P):
        sum_s = np.zeros(nk); sum_c = np.zeros(nk); cnt = np.zeros(nk)
        for i in range(n):
            ss = 0.0; sc = 0
            cs = 0.0; cc = 0
            kis = 0; kic = 0
            svals = np.full(nk, np.nan)
            cvals = np.full(nk, np.nan)
            for idx in range(SORT.shape[1]):
                j = SORT[i, idx]
                if j == i:
                    continue
                gap = abs(scores[j] - scores[i])
                if labels_mat[p, j] == labels_mat[p, i]:
                    if sc < kmax:
                        ss += gap; sc += 1
                        while kis < nk and sc == ks[kis]:
                            svals[kis] = ss / sc; kis += 1
                else:
                    if cc < kmax:
                        cs += gap; cc += 1
                        while kic < nk and cc == ks[kic]:
                            cvals[kic] = cs / cc; kic += 1
                if sc >= kmax and cc >= kmax:
                    break
            for q in range(nk):
                if not (np.isnan(svals[q]) or np.isnan(cvals[q])):
                    sum_s[q] += svals[q]; sum_c[q] += cvals[q]; cnt[q] += 1.0
        for q in range(nk):
            out[p, q] = (sum_c[q] / cnt[q]) / (sum_s[q] / cnt[q])
    return out


@njit(parallel=True)
def boot_lbi(SORT, labels, scores, ks, kmax, counts_mat):
    """Bootstrap LBI_k re-forming neighborhoods inside each replicate.

    counts_mat (B x n): multiplicity of each defendant in the resample. Focal
    defendants weighted by multiplicity; neighbor pool = resampled multiset
    (all copies of the focal itself excluded).
    """
    B = counts_mat.shape[0]
    n = SORT.shape[0]
    nk = len(ks)
    out = np.empty((B, nk))
    for b in prange(B):
        sum_s = np.zeros(nk); sum_c = np.zeros(nk); cnt = np.zeros(nk)
        for i in range(n):
            wi = counts_mat[b, i]
            if wi == 0:
                continue
            ss = 0.0; sc = 0
            cs = 0.0; cc = 0
            kis = 0; kic = 0
            svals = np.full(nk, np.nan)
            cvals = np.full(nk, np.nan)
            for idx in range(SORT.shape[1]):
                j = SORT[i, idx]
                if j == i:
                    continue
                c = counts_mat[b, j]
                if c == 0:
                    continue
                gap = abs(scores[j] - scores[i])
                if labels[j] == labels[i]:
                    m = min(c, kmax - sc)
                    if m > 0:
                        ss += gap * m; sc += m
                        while kis < nk and sc >= ks[kis]:
                            svals[kis] = ss_at(ss, gap, sc, ks[kis], m); kis += 1
                else:
                    m = min(c, kmax - cc)
                    if m > 0:
                        cs += gap * m; cc += m
                        while kic < nk and cc >= ks[kic]:
                            cvals[kic] = ss_at(cs, gap, cc, ks[kic], m); kic += 1
                if sc >= kmax and cc >= kmax:
                    break
            for q in range(nk):
                if not (np.isnan(svals[q]) or np.isnan(cvals[q])):
                    sum_s[q] += wi * svals[q]; sum_c[q] += wi * cvals[q]; cnt[q] += wi
        for q in range(nk):
            out[b, q] = (sum_c[q] / cnt[q]) / (sum_s[q] / cnt[q])
    return out


@njit
def ss_at(total, last_gap, reached, k_target, m_added):
    """Sum-to-k correction when a multiplicity step overshoots the checkpoint."""
    over = reached - k_target
    return (total - last_gap * over) / k_target


@njit(parallel=True)
def distance_matched_lbi(SORT, D, labels, scores, k, n_cand):
    """Same-group comparators explicitly distance-matched to the k cross-group distances."""
    n = SORT.shape[0]
    cg = np.full(n, np.nan); sg = np.full(n, np.nan)
    cdm = np.full(n, np.nan); sdm = np.full(n, np.nan)
    for i in prange(n):
        cross_d = np.empty(k); cross_gap = np.empty(k)
        cand_d = np.empty(n_cand); cand_gap = np.empty(n_cand)
        cc = 0; sc = 0
        for idx in range(SORT.shape[1]):
            j = SORT[i, idx]
            if j == i:
                continue
            if labels[j] != labels[i]:
                if cc < k:
                    cross_d[cc] = D[i, j]; cross_gap[cc] = abs(scores[j] - scores[i]); cc += 1
            else:
                if sc < n_cand:
                    cand_d[sc] = D[i, j]; cand_gap[sc] = abs(scores[j] - scores[i]); sc += 1
            if cc >= k and sc >= n_cand:
                break
        if cc < k or sc < k:
            continue
        ptr = 0
        s_sum = 0.0; sd_sum = 0.0
        for t in range(k):
            target = cross_d[t]
            while ptr + 1 < sc and abs(cand_d[ptr + 1] - target) <= abs(cand_d[ptr] - target):
                ptr += 1
            s_sum += cand_gap[ptr]; sd_sum += cand_d[ptr]
            if ptr + 1 < sc:
                ptr += 1
        cg[i] = cross_gap.mean(); cdm[i] = cross_d.mean()
        sg[i] = s_sum / k; sdm[i] = sd_sum / k
    return cg, sg, cdm, sdm


@njit(parallel=True)
def radius_lbi(SORT, D, labels, scores, radius):
    """Fixed-radius (caliper) neighborhoods instead of fixed k."""
    n = SORT.shape[0]
    cg = np.full(n, np.nan); sg = np.full(n, np.nan)
    for i in prange(n):
        ss = 0.0; sc = 0
        cs = 0.0; cc = 0
        for idx in range(SORT.shape[1]):
            j = SORT[i, idx]
            if j == i:
                continue
            if D[i, j] > radius:
                break
            gap = abs(scores[j] - scores[i])
            if labels[j] == labels[i]:
                ss += gap; sc += 1
            else:
                cs += gap; cc += 1
        if sc >= 1 and cc >= 1:
            sg[i] = ss / sc
            cg[i] = cs / cc
    return cg, sg


def lbi_from_percase(cg, sg, mask=None):
    if mask is None:
        mask = np.ones(len(cg), dtype=bool)
    ok = mask & ~np.isnan(cg) & ~np.isnan(sg)
    return float(np.mean(cg[ok]) / np.mean(sg[ok])), int(ok.sum())


def naive_boot_ci(cg, sg, n_boot=1000, seed=1):
    """Percentile bootstrap over per-focal quantities (neighborhoods fixed) — for supplement."""
    r = np.random.default_rng(seed)
    ok = ~np.isnan(cg) & ~np.isnan(sg)
    c, s = cg[ok], sg[ok]
    m = len(c)
    idx = r.integers(0, m, (n_boot, m))
    vals = c[idx].mean(1) / s[idx].mean(1)
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


results = {"n": n, "cond_number_corr_matrix": cond_number, "seed": SEED,
           "ks": KS.tolist(), "n_perm": N_PERM, "n_boot": N_BOOT}

# =============================================================================
# S0. Standard fairness metrics (manuscript Table 1)
# =============================================================================
recid = df["two_year_recid"].values.astype(int)
std = {}
for gname, mask in (("black", g_race == 1), ("white", g_race == 0)):
    y, hi = recid[mask], bin5[mask].astype(bool)
    std[gname] = {
        "n": int(mask.sum()),
        "base_rate": float(y.mean()),
        "p_highrisk": float(hi.mean()),
        "fpr": float(hi[y == 0].mean()),
        "fnr": float((~hi[y == 1]).mean()),
        "ppv_high": float(y[hi].mean()),
        "p_recid_low": float(y[~hi].mean()),
    }
std["disparate_impact_ratio"] = std["black"]["p_highrisk"] / std["white"]["p_highrisk"]
results["standard_metrics"] = std

# =============================================================================
# S1. Observed LBI, distance diagnostics, focal-group split, gap distribution
# =============================================================================
print("S1: observed + distance diagnostics", flush=True)
zeros = np.zeros(n, dtype=np.int8)
sg_r, cg_r, sd_r, cd_r = walk_all(SORT6, D6, g_race, zeros, False, decile, KS, KMAX)
sg_x, cg_x, sd_x, cd_x = walk_all(SORT6, D6, g_sex, zeros, False, decile, KS, KMAX)

obs = {}
for qi, k in enumerate(KS):
    obs[f"race_k{k}"] = float(np.nanmean(cg_r[:, qi]) / np.nanmean(sg_r[:, qi]))
    obs[f"sex_k{k}"] = float(np.nanmean(cg_x[:, qi]) / np.nanmean(sg_x[:, qi]))
results["observed_lbi"] = obs

# distance diagnostics (R1)
dist_diag = {}
for qi, k in enumerate(KS):
    same_d, cross_d = sd_r[:, qi], cd_r[:, qi]
    dist_diag[f"k{k}"] = {
        "same_mean": float(np.nanmean(same_d)), "cross_mean": float(np.nanmean(cross_d)),
        "same_median": float(np.nanmedian(same_d)), "cross_median": float(np.nanmedian(cross_d)),
        "same_p90": float(np.nanpercentile(same_d, 90)), "cross_p90": float(np.nanpercentile(cross_d, 90)),
        "ratio_of_means": float(np.nanmean(cross_d) / np.nanmean(same_d)),
    }
results["distance_diagnostics"] = dist_diag

# balance diagnostics at k=20: per-feature mean |z-difference| focal-to-neighbor
same_idx, cross_idx = neighbor_idx_k(SORT6, g_race, 20)
bal = {}
for f, name in enumerate(FEATS6):
    z = Xz6[:, f]
    bal[name] = {
        "same": float(np.mean(np.abs(z[same_idx] - z[:, None]))),
        "cross": float(np.mean(np.abs(z[cross_idx] - z[:, None]))),
    }
results["balance_k20_mean_abs_zdiff"] = bal

# common support: propensity overlap
prop_model = LogisticRegression(max_iter=2000).fit(Xz6, g_race)
prop = prop_model.predict_proba(Xz6)[:, 1]
lo_sup = max(prop[g_race == 1].min(), prop[g_race == 0].min())
hi_sup = min(prop[g_race == 1].max(), prop[g_race == 0].max())
in_support = (prop >= lo_sup) & (prop <= hi_sup)
results["common_support"] = {
    "prop_range_black": [float(prop[g_race == 1].min()), float(prop[g_race == 1].max())],
    "prop_range_white": [float(prop[g_race == 0].min()), float(prop[g_race == 0].max())],
    "frac_in_common_support": float(in_support.mean()),
    "lbi_k20_common_support_only": lbi_from_percase(cg_r[:, K20], sg_r[:, K20], in_support)[0],
    "n_common_support": int(in_support.sum()),
}

# caliper exclusion (R1): drop focal cases whose nearest cross-race neighbor is farther
# than the q-th percentile of nearest same-race distances
cal = {}
for q in (90, 75):
    c = np.nanpercentile(sd_r[:, 0], q)
    keep = cd_r[:, 0] <= c
    v, m = lbi_from_percase(cg_r[:, K20], sg_r[:, K20], keep)
    cal[f"q{q}"] = {"caliper": float(c), "n_kept": m, "lbi_k20": v}
results["caliper_analysis"] = cal

# distance-matched specification (R1)
cgm, sgm, cdm, sdm = distance_matched_lbi(SORT6, D6, g_race, decile, 20, 500)
results["distance_matched"] = {
    "lbi_k20": lbi_from_percase(cgm, sgm)[0],
    "ci_naive": naive_boot_ci(cgm, sgm),
    "mean_dist_cross": float(np.nanmean(cdm)), "mean_dist_same_matched": float(np.nanmean(sdm)),
}

# exact felony matching first (R1)
stratF = df["c_charge_F"].values.astype(np.int8)
sgF, cgF, sdF, cdF = walk_all(SORT6, D6, g_race, stratF, True, decile, KS, KMAX)
vF, mF = lbi_from_percase(cgF[:, K20], sgF[:, K20])
results["exact_felony_match"] = {
    "lbi_k20": vF, "n_valid": mF, "ci_naive": naive_boot_ci(cgF[:, K20], sgF[:, K20]),
    "dist_same": float(np.nanmean(sdF[:, K20])), "dist_cross": float(np.nanmean(cdF[:, K20])),
}

# focal-group split + balanced (R8)
focal = {}
for qi, k in enumerate(KS):
    lb, _ = lbi_from_percase(cg_r[:, qi], sg_r[:, qi], g_race == 1)
    lw, _ = lbi_from_percase(cg_r[:, qi], sg_r[:, qi], g_race == 0)
    cb = np.nanmean(cg_r[g_race == 1, qi]); sb = np.nanmean(sg_r[g_race == 1, qi])
    cw = np.nanmean(cg_r[g_race == 0, qi]); sw = np.nanmean(sg_r[g_race == 0, qi])
    focal[f"k{k}"] = {"black_focal": lb, "white_focal": lw,
                      "balanced": float(((cb + cw) / 2) / ((sb + sw) / 2))}
results["focal_groups"] = focal
results["focal_ci_k20"] = {
    "black_focal": naive_boot_ci(np.where(g_race == 1, cg_r[:, K20], np.nan),
                                 np.where(g_race == 1, sg_r[:, K20], np.nan)),
    "white_focal": naive_boot_ci(np.where(g_race == 0, cg_r[:, K20], np.nan),
                                 np.where(g_race == 0, sg_r[:, K20], np.nan)),
}

# gap distribution (R8): per-defendant cross-minus-same mean gap at k=20
delta = cg_r[:, K20] - sg_r[:, K20]
tr = np.nanpercentile(delta, 95)
keep_tr = delta <= tr
results["gap_distribution_k20"] = {
    "mean": float(np.nanmean(delta)), "median": float(np.nanmedian(delta)),
    "q25": float(np.nanpercentile(delta, 25)), "q75": float(np.nanpercentile(delta, 75)),
    "frac_positive": float(np.nanmean(delta > 0)),
    "lbi_trim_top5pct": lbi_from_percase(cg_r[:, K20], sg_r[:, K20], keep_tr)[0],
}

# neighbor reuse + ties (R8)
use_counts = np.bincount(np.concatenate([same_idx.ravel(), cross_idx.ravel()]), minlength=n)
kth = np.take_along_axis(D6, SORT6[:, 20:21].astype(np.int64), axis=1).ravel()
k1th = np.take_along_axis(D6, SORT6[:, 21:22].astype(np.int64), axis=1).ravel()
results["neighbor_reuse"] = {"mean": float(use_counts.mean()), "max": int(use_counts.max()),
                             "p99": float(np.percentile(use_counts, 99))}
results["tie_frac_at_k20_boundary"] = float(np.mean(np.isclose(kth, k1th)))
results["n_duplicate_feature_rows"] = int(n - len(np.unique(Xm6.round(9), axis=0)))

# =============================================================================
# S2. Score representations with raw rates (R4)
# =============================================================================
print("S2: score representations", flush=True)
score_rep = {}
for name, sc in (("decile", decile), ("cat3", cat3), ("bin_ge5", bin5), ("bin_ge8", bin8)):
    sgc, cgc, _, _ = walk_all(SORT6, D6, g_race, zeros, False, sc, KS, KMAX)
    num = float(np.nanmean(cgc[:, K20])); den = float(np.nanmean(sgc[:, K20]))
    score_rep[name] = {"lbi_k20": num / den, "cross_rate": num, "same_rate": den,
                       "ci_naive": naive_boot_ci(cgc[:, K20], sgc[:, K20])}
results["score_representations"] = score_rep

# =============================================================================
# S3. Permutation + CRT + stratified nulls, all k, full n (R2, R7b)
# =============================================================================
print("S3: permutation/CRT/stratified nulls", flush=True)
perm_labels = np.empty((N_PERM, n), dtype=np.int8)
for p in range(N_PERM):
    perm_labels[p] = rng.permutation(g_race)
null_plain = perm_lbi(SORT6, perm_labels, decile, KS, KMAX)

crt_labels = (rng.random((N_PERM, n)) < prop[None, :]).astype(np.int8)
null_crt = perm_lbi(SORT6, crt_labels, decile, KS, KMAX)

strata = np.clip(np.searchsorted(np.quantile(prop, np.linspace(0, 1, 11)[1:-1]), prop), 0, 9)
strat_labels = np.empty((N_PERM, n), dtype=np.int8)
for p in range(N_PERM):
    lab = g_race.copy()
    for s in range(10):
        ii = np.where(strata == s)[0]
        lab[ii] = lab[rng.permutation(ii)]
    strat_labels[p] = lab
null_strat = perm_lbi(SORT6, strat_labels, decile, KS, KMAX)

obs_race = np.array([obs[f"race_k{k}"] for k in KS])
obs_sex = np.array([obs[f"sex_k{k}"] for k in KS])
tests = {}
for tag, nullm in (("plain", null_plain), ("crt", null_crt), ("stratified", null_strat)):
    mu, sdv = nullm.mean(0), nullm.std(0)
    p_point = ((nullm >= obs_race[None, :]).sum(0) + 1) / (N_PERM + 1)
    zobs = (obs_race - mu) / sdv
    znull = (nullm - mu[None, :]) / sdv[None, :]
    p_global = float(((znull.max(1) >= zobs.max()).sum() + 1) / (N_PERM + 1))
    tests[tag] = {"null_mean": mu.tolist(), "null_sd": sdv.tolist(),
                  "p_pointwise": p_point.tolist(), "z": zobs.tolist(), "p_global_maxz": p_global}
results["race_tests"] = tests

# sex: multiscale test under CRT + plain
prop_sex = LogisticRegression(max_iter=2000).fit(Xz6, g_sex).predict_proba(Xz6)[:, 1]
crt_sex = (rng.random((N_PERM, n)) < prop_sex[None, :]).astype(np.int8)
perm_sex = np.empty((N_PERM, n), dtype=np.int8)
for p in range(N_PERM):
    perm_sex[p] = rng.permutation(g_sex)
sex_tests = {}
for tag, labm in (("plain", perm_sex), ("crt", crt_sex)):
    nullm = perm_lbi(SORT6, labm, decile, KS, KMAX)
    mu, sdv = nullm.mean(0), nullm.std(0)
    p_point = ((nullm >= obs_sex[None, :]).sum(0) + 1) / (N_PERM + 1)
    znull = (nullm - mu[None, :]) / sdv[None, :]
    zobs = (obs_sex - mu) / sdv
    p_global = float(((znull.max(1) >= zobs.max()).sum() + 1) / (N_PERM + 1))
    sex_tests[tag] = {"null_mean": mu.tolist(), "null_sd": sdv.tolist(),
                      "p_pointwise": p_point.tolist(), "p_global_maxz": p_global}
results["sex_tests"] = sex_tests

# =============================================================================
# S4. Bootstrap re-forming neighborhoods per replicate (R2)
# =============================================================================
print("S4: neighborhood-recomputing bootstrap", flush=True)
counts = np.zeros((N_BOOT, n), dtype=np.int64)
for b in range(N_BOOT):
    counts[b] = np.bincount(rng.integers(0, n, n), minlength=n)
boot_race = boot_lbi(SORT6, g_race, decile, KS, KMAX, counts)
boot_sex = boot_lbi(SORT6, g_sex, decile, KS, KMAX, counts)
results["boot_recomputed_ci"] = {
    "race": {f"k{k}": [float(np.percentile(boot_race[:, qi], 2.5)),
                       float(np.percentile(boot_race[:, qi], 97.5))] for qi, k in enumerate(KS)},
    "sex": {f"k{k}": [float(np.percentile(boot_sex[:, qi], 2.5)),
                      float(np.percentile(boot_sex[:, qi], 97.5))] for qi, k in enumerate(KS)},
    "race_naive_k20_for_comparison": naive_boot_ci(cg_r[:, K20], sg_r[:, K20]),
}

# =============================================================================
# S5. Matching-method robustness (R5)
# =============================================================================
print("S5: matching-method robustness", flush=True)
method_res = {}

def add_method(name, D, SORT):
    sgc, cgc, _, _ = walk_all(SORT, D, g_race, zeros, False, decile, KS, KMAX)
    v, _ = lbi_from_percase(cgc[:, K20], sgc[:, K20])
    method_res[name] = {"lbi_k20": v, "ci_naive": naive_boot_ci(cgc[:, K20], sgc[:, K20])}

# Euclidean on standardized features
De, Se = dist_sort(Xz6)
add_method("euclidean_standardized", De, Se)
# robust Mahalanobis
_, Xm_rob = whiten(X_raw, robust=True)
Dr, Sr = dist_sort(Xm_rob)
add_method("robust_mahalanobis_mincovdet", Dr, Sr)
# log1p counts then Mahalanobis
X_log = X_raw.copy()
for f in [1, 2, 3, 4]:
    X_log[:, f] = np.log1p(X_log[:, f])
_, Xm_log = whiten(X_log)
Dl, Sl = dist_sort(Xm_log)
add_method("log1p_counts_mahalanobis", Dl, Sl)
# rank transform then Euclidean
X_rank = np.column_stack([rankdata(X_raw[:, f]) / n for f in range(X_raw.shape[1])])
Xr = StandardScaler().fit_transform(X_rank)
Dk, Sk = dist_sort(Xr)
add_method("rank_transform_euclidean", Dk, Sk)
# Gower distance (range-normalized L1; binary mismatch for felony)
rngs = X_raw.max(0) - X_raw.min(0)
Xg = X_raw / rngs
Dg = np.zeros((n, n), dtype=np.float32)
for f in range(X_raw.shape[1]):
    Dg += np.abs(Xg[:, f][:, None] - Xg[:, f][None, :]).astype(np.float32)
Dg /= X_raw.shape[1]
Sg = np.argsort(Dg, axis=1, kind="stable").astype(np.int32)
add_method("gower", Dg, Sg)
results["matching_methods"] = method_res

# coarsened exact matching (age bins, priors bins, juv any-flags, felony)
age_b = np.digitize(df["age"], [21, 25, 30, 35, 40, 50])
pri_b = np.digitize(df["priors_count"], [1, 2, 3, 6, 11])
juv_b = ((df["juv_fel_count"] + df["juv_misd_count"] + df["juv_other_count"]) > 0).astype(int)
cem_stratum = (age_b * 100 + pri_b * 10 + juv_b * 2 + df["c_charge_F"]).values.astype(np.int64)
_, cem_codes = np.unique(cem_stratum, return_inverse=True)
sgC, cgC, _, _ = walk_all(SORT6, D6, g_race, cem_codes.astype(np.int32), True, decile, KS, KMAX)
vC, mC = lbi_from_percase(cgC[:, K20], sgC[:, K20])
results["cem_within_stratum"] = {"lbi_k20": vC, "n_valid_k20": mC,
                                 "ci_naive": naive_boot_ci(cgC[:, K20], sgC[:, K20]),
                                 "n_strata": int(cem_codes.max() + 1)}

# fixed-radius calipers
r_med = float(np.nanmedian(np.take_along_axis(D6, SORT6[:, 20:21].astype(np.int64), axis=1)))
for tag, r in (("median_k20_dist", r_med), ("half_median", r_med / 2)):
    cgr, sgr = radius_lbi(SORT6, D6, g_race, decile, r)
    v, m = lbi_from_percase(cgr, sgr)
    results[f"radius_{tag}"] = {"radius": r, "lbi": v, "n_valid": m,
                                "ci_naive": naive_boot_ci(cgr, sgr)}

# =============================================================================
# S6. Synthetic ground-truth validation (R3)
# =============================================================================
print("S6: synthetic validation", flush=True)
f0_model = LinearRegression().fit(Xz6, decile)
f0 = f0_model.predict(Xz6)
sigma = float(np.std(decile - f0))
results["synthetic_setup"] = {"r2": float(f0_model.score(Xz6, decile)), "sigma_resid": sigma}

# matching space that omits priors_count (condition 4)
FEATS5 = [f for f in FEATS6 if f != "priors_count"]
_, Xm5 = whiten(df[FEATS5].values.astype(np.float64))
D5, SORT5 = dist_sort(Xm5)

same20, cross20 = neighbor_idx_k(SORT6, g_race, 20)
same20_5, cross20_5 = neighbor_idx_k(SORT5, g_race, 20)

def quick_lbi(S, si, ci):
    cmean = np.abs(S[ci] - S[:, None]).mean(1).mean()
    smean = np.abs(S[si] - S[:, None]).mean(1).mean()
    return float(cmean / smean)

def dwork_consistency(S, si, ci):
    """1 - mean |S_i - mean(S of 20 nearest neighbors regardless of group)|, scaled by score SD."""
    allnb = np.concatenate([si, ci], axis=1)
    return float(1.0 - np.mean(np.abs(S - S[allnb].mean(1))) / np.std(S))

def run_condition(tag, score_fn, reps, si, ci, SORTm, n_test=200):
    lbis, rej_plain, rej_crt, rej_reg = [], 0, 0, 0
    k1 = np.array([20], dtype=np.int64)
    for rep in range(reps):
        S = score_fn(np.random.default_rng(SEED + 7919 * rep))
        lb = quick_lbi(S, si, ci)
        lbis.append(lb)
        pl = np.empty((n_test, n), dtype=np.int8)
        rr = np.random.default_rng(SEED + 104729 * rep)
        for p in range(n_test):
            pl[p] = rr.permutation(g_race)
        null_p = perm_lbi(SORTm, pl, S, k1, 20)[:, 0]
        cl = (rr.random((n_test, n)) < prop[None, :]).astype(np.int8)
        null_c = perm_lbi(SORTm, cl, S, k1, 20)[:, 0]
        if (np.sum(null_p >= lb) + 1) / (n_test + 1) < 0.05:
            rej_plain += 1
        if (np.sum(null_c >= lb) + 1) / (n_test + 1) < 0.05:
            rej_crt += 1
        # regression baseline: t on race coefficient
        Xreg = np.column_stack([Xz6, g_race])
        beta, res, _, _ = np.linalg.lstsq(np.column_stack([np.ones(n), Xreg]), S, rcond=None)
        resid = S - np.column_stack([np.ones(n), Xreg]) @ beta
        XtX_inv = np.linalg.inv(np.column_stack([np.ones(n), Xreg]).T @ np.column_stack([np.ones(n), Xreg]))
        se = np.sqrt(XtX_inv[-1, -1] * resid.var(ddof=Xreg.shape[1] + 1))
        if abs(beta[-1] / se) > 1.96:
            rej_reg += 1
    S_last = score_fn(np.random.default_rng(SEED))
    return {"mean_lbi": float(np.mean(lbis)), "sd_lbi": float(np.std(lbis)),
            "reject_rate_plain_perm": rej_plain / reps, "reject_rate_crt": rej_crt / reps,
            "reject_rate_regression": rej_reg / reps,
            "dwork_consistency": dwork_consistency(S_last, si, ci)}

synth = {}
gc_ = g_race.astype(np.float64)
# condition 1: race-blind, race-correlated features
synth["c1_blind"] = run_condition(
    "c1", lambda r: f0 + r.normal(0, sigma, n), 200, same20, cross20, SORT6)
# condition 2: explicit race coefficient (decile units)
for beta in (0.25, 0.5, 1.0):
    synth[f"c2_direct_beta{beta}"] = run_condition(
        f"c2b{beta}", lambda r, b=beta: f0 + b * gc_ + r.normal(0, sigma, n),
        60, same20, cross20, SORT6)
# condition 3: strong proxy (corr ~0.8 with race)
a = 0.8
gz = (gc_ - gc_.mean()) / gc_.std()
for gamma in (0.5, 1.0):
    synth[f"c3_proxy_gamma{gamma}"] = run_condition(
        f"c3g{gamma}", lambda r, g=gamma: f0 + g * (a * gz + np.sqrt(1 - a**2) * r.normal(0, 1, n)) + r.normal(0, sigma, n),
        60, same20, cross20, SORT6)
# condition 4: omitted legitimate predictor (score uses priors; matching does not)
synth["c4_omitted_priors"] = run_condition(
    "c4", lambda r: f0 + r.normal(0, sigma, n), 60, same20_5, cross20_5, SORT5)
results["synthetic"] = synth

# =============================================================================
# S7. Feature-set robustness (carried over, re-run under this pipeline)
# =============================================================================
print("S7: feature-set robustness", flush=True)
featsets = {
    "minimal_age_priors": ["age", "priors_count"],
    "paper6": FEATS6,
    "drop_juvenile": ["age", "priors_count", "c_charge_F"],
    "paper6_plus_sex": FEATS6 + ["male"],
}
fs_res = {}
for name, feats in featsets.items():
    _, Xmf = whiten(df[feats].values.astype(np.float64))
    Df, Sf = dist_sort(Xmf)
    sgc, cgc, _, _ = walk_all(Sf, Df, g_race, zeros, False, decile, KS, KMAX)
    v, _ = lbi_from_percase(cgc[:, K20], sgc[:, K20])
    fs_res[name] = {"lbi_k20": v, "ci_naive": naive_boot_ci(cgc[:, K20], sgc[:, K20])}
results["feature_sets"] = fs_res

# =============================================================================
# save results + figures
# =============================================================================
with open(OUT / "revision2_results.json", "w") as fh:
    json.dump(results, fh, indent=1)
print("results saved", flush=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# fig 1: k-curve with recomputed-bootstrap CIs
fig, ax = plt.subplots(figsize=(7, 4.5))
kk = np.arange(len(KS))
for series, boot, color, label in ((obs_race, boot_race, "#c0392b", "race"),
                                   (obs_sex, boot_sex, "#2980b9", "sex")):
    lo = np.percentile(boot, 2.5, axis=0); hi = np.percentile(boot, 97.5, axis=0)
    ax.errorbar(kk, series, yerr=[np.maximum(series - lo, 0), np.maximum(hi - series, 0)],
                marker="o", capsize=3,
                color=color, label=f"LBI({label})")
ax.axhline(1.0, ls="--", c="gray", lw=1)
ax.set_xticks(kk); ax.set_xticklabels([str(k) for k in KS])
ax.set_xlabel("neighbourhood scale $k$"); ax.set_ylabel("LBI")
ax.legend(); fig.tight_layout(); fig.savefig(FIG / "lbi_by_attribute.pdf"); plt.close(fig)

# fig 2: permutation vs CRT null at k=20
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.hist(null_plain[:, K20], bins=40, alpha=0.55, label="plain permutation null", color="#7f8c8d")
ax.hist(null_crt[:, K20], bins=40, alpha=0.55, label="conditional (CRT) null", color="#27ae60")
ax.axvline(obs_race[K20], color="#c0392b", lw=2, label=f"observed LBI = {obs_race[K20]:.3f}")
ax.set_xlabel("LBI(race) at $k=20$ under null"); ax.set_ylabel("count")
ax.legend(); fig.tight_layout(); fig.savefig(FIG / "lbi_permutation.pdf"); plt.close(fig)

# fig 3: distance diagnostics at k=20 (top 1% clipped so the mass is visible)
sd20 = sd_r[:, K20][~np.isnan(sd_r[:, K20])]
cd20 = cd_r[:, K20][~np.isnan(cd_r[:, K20])]
clip = np.percentile(np.concatenate([sd20, cd20]), 99)
bins = np.linspace(0, clip, 60)
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.hist(np.clip(sd20, 0, clip), bins=bins, alpha=0.6, label="same-race neighbours", color="#2980b9")
ax.hist(np.clip(cd20, 0, clip), bins=bins, alpha=0.6, label="cross-race neighbours", color="#c0392b")
ax.set_xlabel("mean Mahalanobis distance to 20 nearest neighbours (top 1% clipped)")
ax.set_ylabel("defendants"); ax.legend()
fig.tight_layout(); fig.savefig(FIG / "distance_diagnostics.pdf"); plt.close(fig)

# fig 4: gap distribution
fig, ax = plt.subplots(figsize=(7, 4.5))
d = delta[~np.isnan(delta)]
ax.hist(d, bins=60, color="#8e44ad", alpha=0.8)
ax.axvline(0, ls="--", c="gray")
ax.axvline(np.mean(d), c="#c0392b", lw=2, label=f"mean = {np.mean(d):.3f}")
ax.set_xlabel("per-defendant cross-minus-same mean score gap at $k=20$ (decile units)")
ax.set_ylabel("defendants"); ax.legend()
fig.tight_layout(); fig.savefig(FIG / "gap_distribution.pdf"); plt.close(fig)

# fig 5: synthetic validation
fig, ax = plt.subplots(figsize=(7, 4.5))
betas = [0.0, 0.25, 0.5, 1.0]
mlbis = [synth["c1_blind"]["mean_lbi"]] + [synth[f"c2_direct_beta{b}"]["mean_lbi"] for b in betas[1:]]
slbis = [synth["c1_blind"]["sd_lbi"]] + [synth[f"c2_direct_beta{b}"]["sd_lbi"] for b in betas[1:]]
ax.errorbar(betas, mlbis, yerr=2 * np.array(slbis), marker="o", color="#c0392b",
            label="direct race coefficient")
ax.axhline(1.0, ls="--", c="gray", lw=1)
ax.scatter([0], [synth["c4_omitted_priors"]["mean_lbi"]], marker="s", s=60, color="#f39c12",
           zorder=5, label="race-blind, priors omitted from matching")
ax.set_xlabel(r"injected race coefficient $\beta$ (decile units)")
ax.set_ylabel("mean LBI at $k=20$ (semi-synthetic)")
ax.legend(); fig.tight_layout(); fig.savefig(FIG / "synthetic_validation.pdf"); plt.close(fig)

# ---------------------------------------------------------------- text report
def fmt_ci(ci):
    return f"[{ci[0]:.3f}, {ci[1]:.3f}]"

rep = []
rep.append(f"n = {n}; corr-matrix condition number {cond_number:.2f}; seed {SEED}")
rep.append("\n== Standard fairness metrics (Table 1) ==")
for gname in ("black", "white"):
    s = std[gname]
    rep.append(f" {gname:<6} n={s['n']}  base {s['base_rate']:.3f}  P(hi) {s['p_highrisk']:.3f}"
               f"  FPR {s['fpr']:.3f}  FNR {s['fnr']:.3f}  PPV {s['ppv_high']:.3f}"
               f"  P(recid|low) {s['p_recid_low']:.3f}")
rep.append(f" disparate impact ratio {std['disparate_impact_ratio']:.3f}")
rep.append("\n== Observed LBI (k-curve) with neighborhood-recomputing bootstrap CIs ==")
for qi, k in enumerate(KS):
    ci_r = results["boot_recomputed_ci"]["race"][f"k{k}"]
    ci_s = results["boot_recomputed_ci"]["sex"][f"k{k}"]
    rep.append(f" k={k:>3}  race {obs_race[qi]:.3f} {fmt_ci(ci_r)}   sex {obs_sex[qi]:.3f} {fmt_ci(ci_s)}")
rep.append("\n== Distance diagnostics (mean Mahalanobis distance to k nearest) ==")
for k in KS:
    dd = dist_diag[f"k{k}"]
    rep.append(f" k={k:>3}  same {dd['same_mean']:.3f} (med {dd['same_median']:.3f})"
               f"  cross {dd['cross_mean']:.3f} (med {dd['cross_median']:.3f})  ratio {dd['ratio_of_means']:.3f}")
rep.append("\n== Balance at k=20 (mean |z-diff| focal->neighbour) ==")
for f in FEATS6:
    rep.append(f" {f:<18} same {bal[f]['same']:.3f}  cross {bal[f]['cross']:.3f}")
rep.append(f"\ncommon support: {results['common_support']['frac_in_common_support']:.4f} in support;"
           f" LBI k20 in-support {results['common_support']['lbi_k20_common_support_only']:.3f}")
for q, c in cal.items():
    rep.append(f"caliper {q}: kept {c['n_kept']}, LBI k20 {c['lbi_k20']:.3f}")
dm = results["distance_matched"]
rep.append(f"distance-matched: LBI {dm['lbi_k20']:.3f} {fmt_ci(dm['ci_naive'])}"
           f" (dist cross {dm['mean_dist_cross']:.3f} vs same-matched {dm['mean_dist_same_matched']:.3f})")
ef = results["exact_felony_match"]
rep.append(f"exact felony match: LBI {ef['lbi_k20']:.3f} {fmt_ci(ef['ci_naive'])} n={ef['n_valid']}")
rep.append("\n== Score representations at k=20 (raw rates) ==")
for nm, sr in score_rep.items():
    rep.append(f" {nm:<8} LBI {sr['lbi_k20']:.3f} {fmt_ci(sr['ci_naive'])}"
               f"  cross-rate {sr['cross_rate']:.4f}  same-rate {sr['same_rate']:.4f}")
rep.append("\n== Race tests (full n, 1000 reps) ==")
for tag, t in tests.items():
    rep.append(f" {tag:<11} null@k20 {t['null_mean'][K20]:.4f} sd {t['null_sd'][K20]:.4f}"
               f"  p_k20 {t['p_pointwise'][K20]:.4f}  p_global {t['p_global_maxz']:.4f}")
rep.append("== Sex tests ==")
for tag, t in sex_tests.items():
    rep.append(f" {tag:<11} p_k20 {t['p_pointwise'][K20]:.4f}  p_global {t['p_global_maxz']:.4f}"
               f"  p_k1 {t['p_pointwise'][0]:.4f}")
rep.append("\n== Focal groups (k=20) ==")
fk = focal["k20"]
rep.append(f" black-focal {fk['black_focal']:.3f} {fmt_ci(results['focal_ci_k20']['black_focal'])}"
           f"  white-focal {fk['white_focal']:.3f} {fmt_ci(results['focal_ci_k20']['white_focal'])}"
           f"  balanced {fk['balanced']:.3f}")
gd = results["gap_distribution_k20"]
rep.append(f"gap distribution: mean {gd['mean']:.3f} med {gd['median']:.3f}"
           f" frac>0 {gd['frac_positive']:.3f}  trimmed-LBI {gd['lbi_trim_top5pct']:.3f}")
rep.append("\n== Matching methods (k=20) ==")
for nm, mr in method_res.items():
    rep.append(f" {nm:<32} LBI {mr['lbi_k20']:.3f} {fmt_ci(mr['ci_naive'])}")
rep.append(f" CEM within-stratum: LBI {results['cem_within_stratum']['lbi_k20']:.3f}"
           f" {fmt_ci(results['cem_within_stratum']['ci_naive'])} (n_valid {results['cem_within_stratum']['n_valid_k20']})")
for tag in ("radius_median_k20_dist", "radius_half_median"):
    rr_ = results[tag]
    rep.append(f" {tag}: LBI {rr_['lbi']:.3f} {fmt_ci(rr_['ci_naive'])} (n {rr_['n_valid']})")
rep.append("\n== Feature sets (k=20) ==")
for nm, fr in fs_res.items():
    rep.append(f" {nm:<24} LBI {fr['lbi_k20']:.3f} {fmt_ci(fr['ci_naive'])}")
rep.append("\n== Synthetic validation (k=20) ==")
rep.append(f" setup: R2 {results['synthetic_setup']['r2']:.3f} sigma {sigma:.3f}")
for nm, sv in synth.items():
    rep.append(f" {nm:<24} LBI {sv['mean_lbi']:.3f}±{sv['sd_lbi']:.3f}"
               f"  rej: perm {sv['reject_rate_plain_perm']:.2f} crt {sv['reject_rate_crt']:.2f}"
               f" reg {sv['reject_rate_regression']:.2f}")
rep.append(f"\nneighbor reuse: mean {results['neighbor_reuse']['mean']:.1f}"
           f" max {results['neighbor_reuse']['max']}  tie-frac@k20 {results['tie_frac_at_k20_boundary']:.4f}"
           f"  duplicate feature rows: {results['n_duplicate_feature_rows']}")

report = "\n".join(rep)
(OUT / "revision2_report.txt").write_text(report)
print(report, flush=True)
print("\nDONE", flush=True)
