"""Recompute Fraser-Nettle public-goods CIs with the correct contribution column.

The notebook auto-picked Group.Contribution; the manuscript's targets match
the individual `Contribution` column with endowment=20.

Cluster confidence intervals at participant level using a t-statistic on
the per-participant per-round mean.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import t as tdist

BASE = Path(r"C:/source/erisml-lib/docs/papers/foundations/submission/ieee-tcss/tcss_public_data_analysis")
RAW = BASE / "data_raw" / "fraser_nettle_zenodo_3764693"
OUT = BASE / "outputs"

ENDOWMENT = 20.0
df = pd.read_csv(RAW / "Experiment_2.csv", low_memory=False)
# Per-individual contribution rate per round
df["share"] = df["Contribution"] / ENDOWMENT

# Manuscript Table II predictions and observed targets (5 rounds: 1, 3, 5, 8, 10)
FROZEN = {
    1:  ("PG_round_1",  0.500),
    3:  ("PG_round_3",  0.480),
    5:  ("PG_round_5",  0.460),
    8:  ("PG_round_8",  0.430),
    10: ("PG_round_10", 0.400),
}

def round_ci(sub: pd.DataFrame, alpha: float = 0.05):
    """Cluster CI at individual level: t-CI on participant-mean shares."""
    pmean = sub.groupby("UniqueID")["share"].mean()
    n = len(pmean)
    mu = pmean.mean()
    se = pmean.std(ddof=1) / np.sqrt(n)
    tcrit = tdist.ppf(1 - alpha/2, df=n-1)
    return n, mu, mu - tcrit*se, mu + tcrit*se

rows = []
for rnd, (target, pred) in FROZEN.items():
    sub = df[df["Round"] == rnd].dropna(subset=["share"])
    n, mu, lo, hi = round_ci(sub)
    rows.append({
        "target": target, "round": rnd, "n_participants": n,
        "observed": round(mu, 4), "ci_low": round(lo, 4), "ci_high": round(hi, 4),
        "predicted": pred,
        "error_pp": round((pred - mu) * 100, 2),
        "abs_error_pp": round(abs(pred - mu) * 100, 2),
        "in_95ci": (pred >= lo) and (pred <= hi),
    })

# Add ultimatum, dictator, MAO targets from Experiment_1 with bootstrap CIs
exp1 = pd.read_csv(RAW / "Experiment_1.csv", low_memory=False)
# ProposedAmount/10 = ultimatum offer; LowestAcceptable/10 = MAO
rng = np.random.default_rng(20260610)
def boot_ci(x, alpha=0.05, B=10000):
    x = np.asarray(x, dtype=float)
    n = len(x)
    idx = rng.integers(0, n, size=(B, n))
    means = x[idx].mean(axis=1)
    return np.quantile(means, alpha/2), np.quantile(means, 1-alpha/2), x.mean(), n

extra = []
for col, target, pred, scale in [
    ("ProposedAmount",   "UG_mean_offer",        0.480, 10.0),
    ("LowestAcceptable", "Responder_MAO",        0.340, 10.0),
]:
    x = exp1[col].dropna().astype(float) / scale
    lo, hi, mu, n = boot_ci(x.values)
    extra.append({
        "target": target, "round": None, "n_participants": n,
        "observed": round(mu, 4), "ci_low": round(lo, 4), "ci_high": round(hi, 4),
        "predicted": pred,
        "error_pp": round((pred - mu) * 100, 2),
        "abs_error_pp": round(abs(pred - mu) * 100, 2),
        "in_95ci": (pred >= lo) and (pred <= hi),
    })

all_rows = extra + rows
out = pd.DataFrame(all_rows)
print("=== Fraser-Nettle game-target evaluation with correct columns ===")
print(out.to_string(index=False))
out.to_csv(OUT / "fraser_game_evaluation_corrected.csv", index=False)

n_cov = out["in_95ci"].sum()
print(f"\nCI coverage: {n_cov}/{len(out)} = {100*n_cov/len(out):.0f}%")
print(f"Mean abs error (pp): {out['abs_error_pp'].mean():.2f}")

# Also report ultimatum modal offer and dictator giving if columns exist
print("\nUltimatum modal offer (50%):")
mode_val = (exp1["ProposedAmount"] / 10.0)
mode = mode_val.value_counts(normalize=True).sort_values(ascending=False).head(5)
print(mode)
