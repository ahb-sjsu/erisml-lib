"""Re-run the Ruggeri prospect-theory analysis with correct column mapping.

The notebook's alias list missed that the dataset uses bare numeric column names
'1', '3', '7', '11', '16', '17' for the six Kahneman-Tversky problems used as
manuscript prospect-theory targets.

This script:
  1. Loads the Ruggeri modified-exclusions dataset (n=4098, 19 countries).
  2. Maps the six PT targets to numeric columns by item number.
  3. Computes Wilson 95% CIs on observed risky-choice proportions.
  4. Checks whether the manuscript's frozen predictions fall inside each CI.
  5. Computes per-country heterogeneity for each item.
  6. Reports MAE, weighted MAE, and CI-coverage rate.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm

BASE = Path(r"C:/source/erisml-lib/docs/papers/foundations/submission/ieee-tcss/tcss_public_data_analysis")
RAW = BASE / "data_raw" / "ruggeri_osf"
OUT = BASE / "outputs"
OUT.mkdir(exist_ok=True)

# Manuscript Table II OOS prospect-theory predictions (proportion choosing risky):
FROZEN = {
    "1":  ("P1_Allais_certainty",   0.266),
    "3":  ("P3_Strong_certainty",   0.154),
    "7":  ("P7_Reflection",         0.842),
    "11": ("P11_Isolation",         0.154),
    "16": ("P16_Small_prob_gain",   0.507),
    "17": ("P17_Small_prob_loss",   0.506),
}

DATA = RAW / "esxc4_pt_replication_modified_exclusions_data.csv"
df = pd.read_csv(DATA, low_memory=False)
print(f"Loaded Ruggeri modified-exclusions dataset: {df.shape}")
print(f"Columns (first 30): {list(df.columns)[:30]}")

# Identify country column
country_col = None
for cand in ["Country", "country", "Nation", "nation"]:
    if cand in df.columns:
        country_col = cand
        break
print(f"Country column: {country_col}")
if country_col:
    print(f"Countries: {sorted(df[country_col].dropna().unique())}")
    print(f"Per-country n:\n{df.groupby(country_col).size().sort_values()}")

def wilson_ci(k, n, alpha=0.05):
    if n <= 0:
        return (np.nan, np.nan)
    z = norm.ppf(1 - alpha/2)
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2/(2*n)) / denom
    half = (z * np.sqrt(p*(1-p)/n + z**2/(4*n**2))) / denom
    return (center - half, center + half)

# Interpretation of "risky" depends on item coding. The Ruggeri publication
# reports the "replication rate" — i.e., the proportion choosing the same option
# Kahneman & Tversky's original 1979 majorities chose. The numeric columns above
# already represent THAT coding (1 = same as KT majority, 0 = other). For each
# item we want the proportion choosing the RISKY option as the manuscript
# defines it. The risky option in K&T 1979 problems and the K&T-majority option
# do not always coincide, so we check via observed rates from the manuscript.
#
# Manuscript Table II observed rates:
#   P1:  25.5%   Column "1" risky_rate (rate of value=1) = 25.5%  => coding aligned
#   P3:  12.8%   Column "3" risky_rate = 12.8%                    => aligned
#   P7:  79.4%   Column "7" risky_rate = 79.4%                    => aligned
#   P11: 16.1%   Column "11" risky_rate = 16.1%                   => aligned
#   P16: 57.4%   Column "16" risky_rate = 57.4%                   => aligned
#   P17: 42.8%   Column "17" risky_rate = 42.8%                   => aligned
# So column value 1 = chose the risky option per the manuscript's labeling.
# (The match between manuscript observed and Ruggeri raw rates strongly
#  suggests the manuscript already drew its "observed" values from Ruggeri.)

rows = []
for col, (target, pred) in FROZEN.items():
    if col not in df.columns:
        print(f"WARNING column {col!r} missing")
        continue
    x = pd.to_numeric(df[col], errors="coerce").dropna()
    n = len(x)
    k = int(x.sum())
    p = k / n
    lo, hi = wilson_ci(k, n)
    in_ci = (pred >= lo) and (pred <= hi)
    rows.append({
        "target": target, "item": col, "n": n,
        "observed": round(p, 4), "ci_low": round(lo, 4), "ci_high": round(hi, 4),
        "predicted": pred,
        "error_pp": round((pred - p) * 100, 2),
        "abs_error_pp": round(abs(pred - p) * 100, 2),
        "in_95ci": in_ci,
    })
item_df = pd.DataFrame(rows)
print("\n=== Ruggeri item-level evaluation (n=4098) ===")
print(item_df.to_string(index=False))
item_df.to_csv(OUT / "ruggeri_item_evaluation_corrected.csv", index=False)

mae = item_df["abs_error_pp"].mean()
mae_n_weighted = (item_df["abs_error_pp"] * item_df["n"]).sum() / item_df["n"].sum()
coverage = item_df["in_95ci"].mean()
print(f"\nUnweighted MAE (pp): {mae:.3f}")
print(f"Sample-size-weighted MAE (pp): {mae_n_weighted:.3f}")
print(f"95% CI coverage: {item_df['in_95ci'].sum()}/{len(item_df)} = {100*coverage:.1f}%")
print(f"Targets within ±10 pp: {(item_df['abs_error_pp'] <= 10).sum()}/{len(item_df)}")
print(f"Targets within ±5 pp:  {(item_df['abs_error_pp'] <= 5).sum()}/{len(item_df)}")

# ----- Country heterogeneity -----
if country_col is not None:
    print(f"\n=== Per-country evaluation ===")
    crows = []
    for country, sub in df.groupby(country_col):
        if len(sub) < 30:
            continue
        for col, (target, pred) in FROZEN.items():
            if col not in sub.columns:
                continue
            x = pd.to_numeric(sub[col], errors="coerce").dropna()
            if len(x) < 30:
                continue
            n = len(x)
            k = int(x.sum())
            p = k / n
            lo, hi = wilson_ci(k, n)
            crows.append({
                "country": country, "target": target, "item": col,
                "n": n, "observed": round(p, 4),
                "ci_low": round(lo, 4), "ci_high": round(hi, 4),
                "predicted": pred,
                "error_pp": round((pred - p) * 100, 2),
                "abs_error_pp": round(abs(pred - p) * 100, 2),
                "in_95ci": (pred >= lo) and (pred <= hi),
            })
    country_df = pd.DataFrame(crows)
    country_df.to_csv(OUT / "ruggeri_country_evaluation_corrected.csv", index=False)
    # Summary across countries
    print(f"Total country×item cells: {len(country_df)}")
    print(f"CI coverage across cells: {country_df['in_95ci'].sum()}/{len(country_df)} "
          f"= {100*country_df['in_95ci'].mean():.1f}%")
    print(f"Cells with |error|>10pp: {(country_df['abs_error_pp']>10).sum()}/{len(country_df)} "
          f"= {100*(country_df['abs_error_pp']>10).mean():.1f}%")
    # Per-item country spread
    print("\n=== Cross-country spread per item ===")
    by_item = country_df.groupby("target").agg(
        n_countries=("country", "nunique"),
        obs_min=("observed", "min"),
        obs_max=("observed", "max"),
        obs_range_pp=("observed", lambda s: (s.max()-s.min())*100),
        pred=("predicted", "first"),
        mean_abs_err_pp=("abs_error_pp", "mean"),
        max_abs_err_pp=("abs_error_pp", "max"),
        ci_coverage=("in_95ci", "mean"),
    )
    print(by_item.round(3).to_string())

    # Per-country mean MAE
    print("\n=== Per-country MAE (across 6 items) ===")
    by_country = country_df.groupby("country").agg(
        n_responses=("n", "mean"),
        mae_pp=("abs_error_pp", "mean"),
        ci_coverage=("in_95ci", "mean"),
    ).sort_values("mae_pp")
    print(by_country.round(2).to_string())

print("\nDone.")
