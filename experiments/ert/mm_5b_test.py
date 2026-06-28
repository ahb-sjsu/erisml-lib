#!/usr/bin/env python3
"""ERT Falsifier 5b on Moral Machine AMCE preferences (summary_overall_preferences.csv).
Each agent (176 LLMs + 1 aggregate Human) = a load configuration with a labeled 9-D
moral-preference vector. ERT 5b predicts: (A) agent references cluster into >=2 basins,
and (B) multimodality concentrates on SACRED/identity dimensions (who someone is:
age/gender/status/species/fitness) over IMPARTIAL ones (number/intervention/law/relation).
NOTE: population is AI models, not human cultures — informs but does not strictly satisfy
the country-level pre-registration. Nulls reported honestly."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "src"); from erisml.ethics.governance.consensus import _gmm_dbic, _sarle_bc
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from scipy.stats import mannwhitneyu

df = pd.read_csv("experiments/ert/mm_data/mm_unzip/summary_overall_preferences.csv", index_col=0)
dims = list(df.index); agents = list(df.columns)
A = df.T.values.astype(float)                      # 177 agents x 9 dims
print(f"agents: {len(agents)} (incl. {'Human' if 'Human' in agents else 'NO human'})  dims: {dims}")
SACRED = {"Age", "Fitness", "Gender", "Social Status", "Species"}

Az = (A - A.mean(0)) / (A.std(0) + 1e-9)           # z-scored for shape-based clustering
print("\n== Test A: do agent references cluster into >=2 basins? ==")
bics = {k: GaussianMixture(k, n_init=8, random_state=0).fit(Az).bic(Az) for k in (1, 2, 3, 4)}
for k, b in bics.items(): print(f"  GMM k={k}: BIC={b:.1f}")
best = min(bics, key=bics.get); print(f"  -> BIC-optimal #components: {best}")
for k in (2, 3, 4):
    lab = KMeans(k, n_init=8, random_state=0).fit_predict(Az)
    print(f"  k={k} silhouette={silhouette_score(Az, lab):.3f}")
C = Az - Az.mean(0); _, _, Vt = np.linalg.svd(C, full_matrices=False); pc1 = C @ Vt[0]
print(f"  principal-axis dBIC={_gmm_dbic(pc1):+.1f}  Sarle={_sarle_bc(pc1):.3f}")

print("\n== Test B: is bimodality concentrated on SACRED/identity dims? ==")
rows = []
for i, d in enumerate(dims):
    x = A[:, i]
    rows.append((d, _gmm_dbic(x), _sarle_bc(x), float(x.std()), d in SACRED))
for d, db, bc, sd, sac in sorted(rows, key=lambda r: -r[2]):
    print(f"  {d:16s} {'SACRED' if sac else 'impart'}  dBIC={db:+8.1f}  Sarle={bc:.3f}  std={sd:.3f}")
sac_bc = [bc for _, db, bc, sd, s in rows if s]; imp_bc = [bc for _, db, bc, sd, s in rows if not s]
sac_db = [db for _, db, bc, sd, s in rows if s]; imp_db = [db for _, db, bc, sd, s in rows if not s]
_, p_bc = mannwhitneyu(sac_bc, imp_bc, alternative="greater")
_, p_db = mannwhitneyu(sac_db, imp_db, alternative="greater")
print(f"\n  Mann-Whitney sacred > impartial  | Sarle (scale-free): p={p_bc:.4f}")
print(f"  Mann-Whitney sacred > impartial  | dBIC:               p={p_db:.4f}")
print(f"  (n=5 sacred vs 4 impartial dims; min achievable one-sided p = 1/126 = 0.0079)")

print("\n== KILL CRITERION ==")
basins = best >= 2 and silhouette_score(Az, KMeans(2, n_init=8, random_state=0).fit_predict(Az)) > 0.15
print(f"  A) >=2 stable basins: {'PASS' if basins else 'FAIL'} (BIC-opt={best})")
print(f"  B) sacred-axis concentration p<0.01: {'PASS' if min(p_bc,p_db)<0.01 else 'FAIL'} (best p={min(p_bc,p_db):.4f})")
print(f"  -> {'CONFIRM' if (basins and min(p_bc,p_db)<0.01) else 'NOT CONFIRMED'}")
