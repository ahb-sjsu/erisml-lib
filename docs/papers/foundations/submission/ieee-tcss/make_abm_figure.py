"""Generate the agent-based worked-example illustration referenced as Fig. abm."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

OUT = r"C:\source\erisml-lib\docs\papers\foundations\submission\ieee-tcss\figures"
os.makedirs(OUT, exist_ok=True)

rng = np.random.default_rng(20260610)
N = 2000
offers = np.linspace(0.0, 0.5, 51)

def softmax_probs(costs, T=0.5):
    z = -np.asarray(costs) / T
    z -= z.max()
    p = np.exp(z); return p / p.sum()

s6, s7, s9 = 78.26, 32.28, 0.01262
def geom_cost(x):
    return np.sqrt(x**2/s6 + x**2/s7 + (0.80-0.80)**2/s9 + (0.5-x)**2/s6)
geom_p = softmax_probs([geom_cost(x) for x in offers], T=0.5)
geom_sample = rng.choice(offers, size=N, p=geom_p)

ev_p = np.zeros_like(offers); ev_p[0] = 1.0
ev_sample = rng.choice(offers, size=N, p=ev_p) + rng.normal(0, 0.005, size=N)

alpha = rng.uniform(0.0, 1.5, size=N); beta = rng.uniform(0.0, 0.7, size=N)
fs_offers = np.clip(0.5 - beta/(2*(alpha+beta+1e-6)), 0.0, 0.5)
fs_sample = fs_offers + rng.normal(0, 0.02, size=N)

fig, ax = plt.subplots(figsize=(3.5, 2.5))
bins = np.linspace(0, 0.55, 30)
ax.hist(ev_sample, bins=bins, alpha=0.45, color="#888", label="EV-max agent", density=True)
ax.hist(fs_sample, bins=bins, alpha=0.45, color="#4477AA", label="Fehr--Schmidt", density=True)
ax.hist(geom_sample, bins=bins, alpha=0.55, color="#CC6677", label="Geometric primitive", density=True)
ax.axvline(0.48, ls=":", color="black", lw=0.8)
ax.text(0.48, ax.get_ylim()[1]*0.92, " observed UG mean", fontsize=7, va="top")
ax.set_xlabel("Ultimatum offer (share)")
ax.set_ylabel("Density")
ax.set_xlim(0, 0.55)
ax.legend(loc="upper left", fontsize=7, framealpha=0.9)
ax.set_title("Agent-based illustration (not a new validation)")
fig.savefig(os.path.join(OUT, "abm_worked_example.pdf"))
fig.savefig(os.path.join(OUT, "abm_worked_example.png"))
print("Saved abm_worked_example.{pdf,png}")
