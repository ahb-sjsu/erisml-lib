"""Generate a predicted-vs-observed plot with corrected CIs for both domains."""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

BASE = Path(r"C:/source/erisml-lib/docs/papers/foundations/submission/ieee-tcss/tcss_public_data_analysis")
OUT = BASE / "outputs"
FIG = OUT / "figures"
FIG.mkdir(exist_ok=True)

ru = pd.read_csv(OUT / "ruggeri_item_evaluation_corrected.csv")
fn = pd.read_csv(OUT / "fraser_game_evaluation_corrected.csv")

fig, ax = plt.subplots(figsize=(7, 7))

# Game targets (Fraser-Nettle)
yerr_lo = (fn["observed"] - fn["ci_low"]).values * 100
yerr_hi = (fn["ci_high"] - fn["observed"]).values * 100
ax.errorbar(fn["observed"] * 100, fn["predicted"] * 100,
            xerr=[yerr_lo, yerr_hi], fmt="o", color="tab:blue",
            label="Game (Fraser-Nettle, IS calibration)", capsize=3, ms=8)

# Prospect-theory targets (Ruggeri)
yerr_lo = (ru["observed"] - ru["ci_low"]).values * 100
yerr_hi = (ru["ci_high"] - ru["observed"]).values * 100
ax.errorbar(ru["observed"] * 100, ru["predicted"] * 100,
            xerr=[yerr_lo, yerr_hi], fmt="^", color="tab:red",
            label="Prospect theory (Ruggeri n=4098, OOS)", capsize=3, ms=10)

# Label each PT point
for _, r in ru.iterrows():
    ax.annotate(r["target"].replace("_", "\n"),
                (r["observed"]*100, r["predicted"]*100),
                xytext=(7, 0), textcoords="offset points",
                fontsize=7, color="tab:red")

# Reference lines
lims = [10, 90]
ax.plot(lims, lims, "k--", lw=1, label="Perfect")
ax.fill_between(lims, [l-5 for l in lims], [l+5 for l in lims], color="green", alpha=0.08, label="±5 pp")
ax.fill_between(lims, [l-10 for l in lims], [l+10 for l in lims], color="green", alpha=0.04, label="±10 pp")

ax.set_xlim(lims); ax.set_ylim(lims)
ax.set_xlabel("Observed % (with 95% CI bars)")
ax.set_ylabel("Predicted %")
ax.set_title("Geometric prediction vs public-data observed rates\n"
             "Game side: 6/7 within CI; Prospect-theory side: 2/6 within CI")
ax.legend(loc="upper left", fontsize=9)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(FIG / "predicted_vs_observed_public_data.png", dpi=150)
plt.savefig(FIG / "predicted_vs_observed_public_data.pdf")
print(f"Saved: {FIG / 'predicted_vs_observed_public_data.png'}")
