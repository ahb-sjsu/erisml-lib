#!/usr/bin/env python3
"""ERT bifurcation figure: (a) pitchfork of the moral reference vs dispersion;
(b) the exact schism-stiffness h_kappa(delta)=sqrt(k) d cot(sqrt(k) d) that
vanishes at the threshold (the critical-slowing-down curve of section 5.7)."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, (axA, axB) = plt.subplots(1, 2, figsize=(9, 3.6))

# ---- Panel (a): pitchfork bifurcation (normal-form schematic) ----
mu = np.linspace(0, 1.8, 400)          # control parameter rho/rho*
# stable central branch (mu<1) then unstable (mu>1)
axA.plot(mu[mu <= 1], 0*mu[mu <= 1], color="C0", lw=2.4, label="stable reference")
axA.plot(mu[mu > 1], 0*mu[mu > 1], color="C3", lw=1.6, ls="--", label="unstable (saddle)")
mu2 = mu[mu > 1]
branch = 1.25*np.sqrt(mu2 - 1)         # +/- stable branches
axA.plot(mu2, branch, color="C0", lw=2.4)
axA.plot(mu2, -branch, color="C0", lw=2.4)
axA.axvline(1, color="gray", ls=":", lw=1)
axA.text(1.02, 1.32, r"schism threshold $\rho^{*}$", fontsize=8, color="gray")
axA.text(0.18, 0.10, "one neutral\n(pluralism)", fontsize=8, ha="center")
axA.text(1.45, 1.05, "two references\n(schism)", fontsize=8, ha="center", color="C0")
axA.set_xlabel(r"dispersion $\rho/\rho^{*}\;(=\sqrt{\kappa}\,\delta\,/\,(\pi/2))$")
axA.set_ylabel("reference position (perp. coord.)")
axA.set_title("(a) Bifurcation of the moral reference")
axA.legend(fontsize=7, loc="lower left")
axA.set_ylim(-1.7, 1.7)

# ---- Panel (b): exact schism stiffness h(u)=u cot(u), u=sqrt(k)*delta ----
u = np.linspace(1e-3, np.pi-1e-3, 600)
h = u/np.tan(u)                         # u*cot(u)
axB.axhspan(0, 2, color="C2", alpha=0.08)
axB.axhspan(-3, 0, color="C3", alpha=0.08)
axB.plot(u, h, color="k", lw=2)
axB.axhline(0, color="gray", lw=0.8)
axB.axvline(np.pi/2, color="gray", ls=":", lw=1)
axB.text(np.pi/2+0.05, 0.55, r"threshold $\sqrt{\kappa}\,\delta=\pi/2$", fontsize=8, color="gray")
axB.text(0.35, 0.62, "unique reference\n($h>0$, stable)", fontsize=8, color="C2")
axB.text(2.05, -1.6, "schism\n($h<0$)", fontsize=8, color="C3")
axB.set_xlabel(r"$\sqrt{\kappa}\,\delta$  (curvature $\times$ half-separation)")
axB.set_ylabel(r"schism stiffness  $h_\kappa(\delta)=\sqrt{\kappa}\,\delta\cot(\sqrt{\kappa}\,\delta)$")
axB.set_title("(b) Stiffness vanishes at threshold (slowing-down)")
axB.set_ylim(-2.5, 1.2); axB.set_xlim(0, np.pi)

fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(f"ert_bifurcation.{ext}", dpi=150, bbox_inches="tight")
print("wrote ert_bifurcation.pdf / .png")
