"""Replace the Andersen high-stakes cells (36-39) with a tighter analysis aimed
at the TCSS manuscript's *stake-scaling-invariance* prediction.

The current cells were generic scaffolding written before the data arrived.
With the actual Andersen-Ertac-Gneezy-Hoffman-List (2011) data in hand we
can do the exact test the TCSS reviewer asked for:

The manuscript's "money-zero" result (sigma^2_1 = inf) implies stake-scaling
invariance — multiplying all monetary stakes by a constant should leave
predictions unchanged. Andersen et al. (2011) studied stakes from Rs 20 to
Rs 20,000 (a 1000x range, max ~1.6x monthly income in Indonesia).

If money-zero is universal, mean percent_offer and rejection-rate-conditional-
on-percent-offer should be invariant across stakes. If money-zero is a
boundary condition (manuscript's softened revision claim), both should change.

This analysis tests that directly.
"""
from __future__ import annotations
import json
from pathlib import Path

NB = Path(r"C:/source/erisml-lib/docs/papers/foundations/submission/ieee-tcss/tcss_public_data_analysis.ipynb")
nb = json.loads(NB.read_text(encoding="utf-8"))

# ------------- New markdown cell (the existing markdown cell 35 stays) -------------

# We will REPLACE cells 36, 37, 38, 39 with new self-contained cells.

# ---- New Cell 36 (load Andersen .dta and filter to IN==1 by default) ----
new_36 = '''# Load Andersen et al. (2011) "Stakes Matter in Ultimatum Games" data.
# The .dta also contains pooled Slonim-Roth (SR) and Cameron (C) re-analysis
# rows; the published headline analysis uses Andersen's own subset (IN==1).
ANDERSEN_DTA = openicpsr_dir / OPENICPSR_DTA_FILENAME
ANDERSEN_INCLUDE_POOLED = False  # set True to use all three studies via DaysW

def load_andersen_data() -> pd.DataFrame | None:
    if not ANDERSEN_DTA.exists():
        print(f"Andersen .dta not at {ANDERSEN_DTA}.")
        print("Manual: download the openICPSR 112485 archive or place 20100982_DATA.dta there.")
        return None
    df = pd.read_stata(ANDERSEN_DTA, convert_categoricals=False)
    print(f"Loaded {df.shape[0]} rows, columns: {list(df.columns)}")
    if ANDERSEN_INCLUDE_POOLED:
        sub = df.copy()
        sub["study"] = np.where(sub["IN"]==1, "Andersen", np.where(sub["SR"]==1, "Slonim-Roth", "Cameron"))
    else:
        sub = df[df["IN"]==1].copy()
        sub["study"] = "Andersen"
    sub["reject"] = 1 - sub["accept"]
    sub = sub.dropna(subset=["stakes", "percent_offer", "accept"])
    print(f"Working sample: n={len(sub)} ({'pooled' if ANDERSEN_INCLUDE_POOLED else 'Andersen IN==1 only'})")
    print(f"Stakes levels: {sorted(sub['stakes'].unique())}")
    return sub

andersen_df = load_andersen_data()
if andersen_df is not None:
    display(andersen_df.head())
'''

# ---- New Cell 37 (descriptive stats by stakes — the falsification table) ----
new_37 = '''# Descriptive: mean percent_offer and rejection rate per stakes level.
# Under the manuscript's stake-scaling invariance (sigma^2_1 = inf, d_1 inactive),
# both columns should be flat across stakes.

if andersen_df is None or andersen_df.empty:
    andersen_summary = pd.DataFrame()
else:
    rows = []
    for stake, sub in andersen_df.groupby("stakes"):
        n = len(sub)
        po = sub["percent_offer"]
        rj = sub["reject"]
        # CIs on means
        po_se = po.std(ddof=1) / np.sqrt(n)
        rj_se = np.sqrt(rj.mean() * (1 - rj.mean()) / n)
        rows.append({
            "stakes": int(stake),
            "n": n,
            "mean_percent_offer": po.mean(),
            "po_ci_low": po.mean() - 1.96*po_se,
            "po_ci_high": po.mean() + 1.96*po_se,
            "mean_reject": rj.mean(),
            "rj_ci_low": rj.mean() - 1.96*rj_se,
            "rj_ci_high": rj.mean() + 1.96*rj_se,
            # Rejection rate restricted to "unfair" offers (<=20% of pie)
            "reject_unfair_offers": rj[sub["percent_offer"] <= 0.201].mean()
                if (sub["percent_offer"] <= 0.201).any() else np.nan,
            "n_unfair_offers": int((sub["percent_offer"] <= 0.201).sum()),
        })
    andersen_summary = pd.DataFrame(rows).sort_values("stakes")
    andersen_summary.to_csv(OUT_DIR / "andersen_stakes_summary.csv", index=False)
    display(andersen_summary.round(3))

    # Geometric model's stake-scaling-invariance prediction is *flat*. Compute
    # the average prediction (mean of observed percent_offer at stake==20) and
    # report deviations at higher stakes.
    if not andersen_summary.empty:
        baseline_offer = andersen_summary.loc[andersen_summary["stakes"]==20, "mean_percent_offer"].iloc[0]
        baseline_reject = andersen_summary.loc[andersen_summary["stakes"]==20, "mean_reject"].iloc[0]
        andersen_summary["po_dev_from_baseline_pp"] = (andersen_summary["mean_percent_offer"] - baseline_offer) * 100
        andersen_summary["rj_dev_from_baseline_pp"] = (andersen_summary["mean_reject"] - baseline_reject) * 100
        print("\\nGeometric stake-scaling-invariance prediction: zero deviation across stakes.")
        print(andersen_summary[["stakes", "mean_percent_offer", "po_dev_from_baseline_pp",
                                  "mean_reject", "rj_dev_from_baseline_pp"]].round(3).to_string(index=False))
'''

# ---- New Cell 38 (formal test: chi-square + logit) ----
new_38 = '''# Formal tests of stake invariance.
# (a) Chi-square test of equal rejection rates across stakes (Andersen Table 2)
# (b) ANOVA / Kruskal on percent_offer across stakes
# (c) Logit reject ~ percent_offer + log_stake  -- LRT for log_stake coefficient

from scipy.stats import chi2_contingency, kruskal, chi2

def test_stake_invariance(d: pd.DataFrame) -> dict:
    if d is None or d.empty:
        return {}
    # Chi-square on rejection-by-stake contingency
    ct = pd.crosstab(d["stakes"], d["reject"])
    chi2_stat, p_chi2, dof, _ = chi2_contingency(ct)

    # Kruskal-Wallis on percent_offer across stakes
    groups = [g["percent_offer"].values for _, g in d.groupby("stakes")]
    h_stat, p_kw = kruskal(*groups)

    # Logit: reject ~ percent_offer + log(stake)
    dd = d.copy()
    dd["log_stake"] = np.log(dd["stakes"])
    dd["offer_share"] = dd["percent_offer"].clip(1e-6, 1-1e-6)
    m0 = smf.logit("reject ~ offer_share", data=dd).fit(disp=False)
    m1 = smf.logit("reject ~ offer_share + log_stake", data=dd).fit(disp=False)
    lr = 2 * (m1.llf - m0.llf)
    p_lr = float(chi2.sf(lr, df=1))

    return {
        "n": len(d),
        "chi2_reject_by_stake": chi2_stat, "p_chi2": p_chi2,
        "kruskal_offer_by_stake_H": h_stat, "p_kruskal": p_kw,
        "logit_log_stake_coef": float(m1.params.get("log_stake", np.nan)),
        "logit_log_stake_se":   float(m1.bse.get("log_stake", np.nan)),
        "logit_log_stake_OR":   float(np.exp(m1.params.get("log_stake", np.nan))),
        "logit_log_stake_p":    float(m1.pvalues.get("log_stake", np.nan)),
        "LRT_p_stake_vs_offer": p_lr,
        "logit_baseline_aic": float(m0.aic), "logit_with_stake_aic": float(m1.aic),
    }, m0, m1

if andersen_df is not None and not andersen_df.empty:
    invariance_tests, m_offer_only, m_with_stake = test_stake_invariance(andersen_df)
    print("\\nStake-invariance test results:")
    for k, v in invariance_tests.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4g}")
        else:
            print(f"  {k}: {v}")
    pd.Series(invariance_tests, name="value").to_csv(OUT_DIR / "andersen_invariance_tests.csv")

    print("\\nLogit with log(stakes):")
    print(m_with_stake.summary().tables[1])
else:
    invariance_tests = {}
'''

# ---- New Cell 39 (the money-zero falsification figure) ----
new_39 = '''# Money-zero falsification figure.
# Two panels: (1) mean percent_offer by stake, (2) rejection rate by stake,
# both with 95% CIs and the geometric framework's flat-line prediction.

if andersen_df is not None and not andersen_df.empty and not andersen_summary.empty:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    s = andersen_summary.sort_values("stakes")
    x = np.arange(len(s))
    labels = [f"Rs {int(v):,}" for v in s["stakes"]]

    # Panel 1: percent offer
    ax = axes[0]
    yerr = [(s["mean_percent_offer"] - s["po_ci_low"]).values,
            (s["po_ci_high"] - s["mean_percent_offer"]).values]
    ax.bar(x, s["mean_percent_offer"]*100, yerr=np.array(yerr)*100, capsize=4,
           color="#4477AA", label="Observed (mean ± 95% CI)")
    baseline = s["mean_percent_offer"].iloc[0] * 100
    ax.axhline(baseline, ls="--", color="red",
               label=f"Geometric stake-scaling invariance ({baseline:.1f}%)")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=20)
    ax.set_ylabel("Mean offer (% of pie)")
    ax.set_title("(a) Proposer behavior by stakes")
    ax.legend(fontsize=9)
    ax.set_ylim(0, max(35, baseline*1.5))
    ax.grid(axis="y", alpha=0.3)

    # Panel 2: rejection rate
    ax = axes[1]
    yerr = [(s["mean_reject"] - s["rj_ci_low"]).values,
            (s["rj_ci_high"] - s["mean_reject"]).values]
    ax.bar(x, s["mean_reject"]*100, yerr=np.array(yerr)*100, capsize=4,
           color="#CC6677", label="Observed (mean ± 95% CI)")
    baseline_r = s["mean_reject"].iloc[0] * 100
    ax.axhline(baseline_r, ls="--", color="red",
               label=f"Geometric stake-scaling invariance ({baseline_r:.1f}%)")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=20)
    ax.set_ylabel("Rejection rate (%)")
    ax.set_title("(b) Responder behavior by stakes")
    ax.legend(fontsize=9)
    ax.set_ylim(0, max(50, baseline_r*1.5))
    ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Andersen et al. (2011) high-stakes ultimatum: money-zero boundary",
                 fontsize=12, y=1.02)
    fig.tight_layout()
    path = FIG_DIR / "andersen_money_zero_falsification.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    fig.savefig(FIG_DIR / "andersen_money_zero_falsification.pdf", bbox_inches="tight")
    print(f"Saved: {path}")
else:
    print("No Andersen data — figure skipped.")
'''

new_cells = [new_36, new_37, new_38, new_39]
for idx, src in zip([36, 37, 38, 39], new_cells):
    nb["cells"][idx]["source"] = src.splitlines(keepends=True)
    nb["cells"][idx]["outputs"] = []
    nb["cells"][idx]["execution_count"] = None

# Clear outputs across the notebook so re-execution is clean
for c in nb["cells"]:
    if c["cell_type"] == "code":
        c["outputs"] = []
        c["execution_count"] = None

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Replaced cells 36-39 in {NB}")
