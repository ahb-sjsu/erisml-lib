#!/usr/bin/env python3
"""ERT falsifier 5 on real moral judgments (AITA, n=2922).

ERT schism claim: where a community's verdict SPLITS, the moral-position
distribution should be BIMODAL (two references / a bifurcated neutral), not merely
a higher-variance unimodal blob. Test: cluster posts by topic; per topic measure
contestation (verdict entropy) and bimodality of the moral-position projection
(Gaussian-mixture 1-vs-2 BIC + Sarle's coefficient). ERT predicts contestation
tracks BIMODALITY beyond what dispersion alone explains. Honest nulls reported."""
import numpy as np, csv, json
from collections import Counter
np.random.seed(0)
rows=list(csv.DictReader(open("data/AITA_labeled_posts.csv",encoding="utf-8",errors="replace")))
texts=[((r["post_title"] or "")+". "+(r["post_content"] or "")[:1200]) for r in rows]
verd=np.array([r["verdict"].strip().upper() for r in rows])
print("verdict counts:",dict(Counter(verd)))

# ---- embed (cache) ----
import os
import os
MODEL=os.environ.get("ERT_MODEL","BAAI/bge-small-en-v1.5")
cache=f"experiments/ert/aita_emb_{MODEL.split(chr(47))[-1]}.npy"
if os.path.exists(cache):
    emb=np.load(cache)
else:
    from sentence_transformers import SentenceTransformer
    m=SentenceTransformer(MODEL)
    emb=m.encode(texts,normalize_embeddings=True,batch_size=64,show_progress_bar=True)
    np.save(cache,emb)
print("emb:",emb.shape)

# ---- moral discriminant axis: YTA(1) vs NTA(0) ----
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
bin_mask=np.isin(verd,["YTA","NTA"]); y=(verd[bin_mask]=="YTA").astype(int)
X=emb[bin_mask]
auc=cross_val_score(LogisticRegression(max_iter=2000,C=1.0),X,y,scoring="roc_auc",cv=5).mean()
clf=LogisticRegression(max_iter=2000,C=1.0).fit(X,y)
axis=clf.coef_[0]/np.linalg.norm(clf.coef_[0])
pos=emb@axis                                  # moral position for ALL posts
print(f"moral-axis YTA-vs-NTA 5-fold AUC = {auc:.3f}  (>0.6 => recoverable moral axis)")

# ---- topic clusters (KMeans on embeddings) ----
from sklearn.cluster import KMeans
K=30
lab=KMeans(K,n_init=5,random_state=0).fit_predict(emb)

# ---- per-topic: contestation vs bimodality ----
from sklearn.mixture import GaussianMixture
def sarle_bc(x):
    n=len(x); 
    if n<8: return np.nan
    s=((x-x.mean())**3).mean()/x.std()**3
    k=((x-x.mean())**4).mean()/x.std()**4
    return (s**2+1)/(k+3*(n-1)**2/((n-2)*(n-3)))
def gmm_dbic(x):                              # BIC(1)-BIC(2); >0 => 2 comps preferred
    x=x.reshape(-1,1)
    if len(x)<12: return np.nan
    b1=GaussianMixture(1,random_state=0).fit(x).bic(x)
    b2=GaussianMixture(2,n_init=3,random_state=0).fit(x).bic(x)
    return b1-b2
recs=[]
for c in range(K):
    idx=lab==c; n=int(idx.sum())
    vb=verd[idx]; nbin=np.isin(vb,["YTA","NTA"]).sum()
    if n<20 or nbin<10: continue
    p=(vb=="YTA").sum()/max(1,np.isin(vb,["YTA","NTA"]).sum())
    ent=0.0 if p in(0,1) else -(p*np.log2(p)+(1-p)*np.log2(1-p))   # verdict entropy
    pc=pos[idx]
    recs.append(dict(c=c,n=n,yta_frac=round(float(p),3),entropy=round(float(ent),3),
                     dispersion=round(float(pc.std()),4),
                     dbic=round(float(gmm_dbic(pc)),2),bc=round(float(sarle_bc(pc)),3)))
recs=[r for r in recs if not (np.isnan(r["dbic"]) or np.isnan(r["bc"]))]
print(f"\nusable topics: {len(recs)}")
ent=np.array([r["entropy"] for r in recs]); disp=np.array([r["dispersion"] for r in recs])
dbic=np.array([r["dbic"] for r in recs]); bc=np.array([r["bc"] for r in recs])
from scipy.stats import pearsonr, spearmanr
def corr(a,b,lbl):
    r,p=spearmanr(a,b); print(f"  spearman {lbl:28s} rho={r:+.3f}  p={p:.3f}")
print("\n== ERT prediction: contestation tracks BIMODALITY ==")
corr(ent,dbic,"entropy vs GMM dBIC")
corr(ent,bc,"entropy vs Sarle BC")
corr(ent,disp,"entropy vs dispersion (control)")
# partial: does entropy predict bimodality beyond dispersion?
import numpy as np
def partial_spear(a,b,ctrl):
    # residualize ranks
    from scipy.stats import rankdata
    A,B,C=rankdata(a),rankdata(b),rankdata(ctrl)
    ra=A-np.polyval(np.polyfit(C,A,1),C); rb=B-np.polyval(np.polyfit(C,B,1),C)
    r,p=pearsonr(ra,rb); return r,p
pr,pp=partial_spear(ent,dbic,disp)
print(f"  partial (entropy vs dBIC | dispersion)      rho={pr:+.3f}  p={pp:.3f}")
# contested vs consensus split
hi=[r for r in recs if r["entropy"]>=0.8]; lo=[r for r in recs if r["entropy"]<0.5]
def frac_bimodal(g): return np.mean([1 if r["dbic"]>0 else 0 for r in g]) if g else float("nan")
print(f"\ncontested topics (entropy>=0.8): {len(hi)}  frac GMM-bimodal={frac_bimodal(hi):.2f}  mean BC={np.mean([r['bc'] for r in hi]):.3f}")
print(f"consensus topics (entropy<0.5):  {len(lo)}  frac GMM-bimodal={frac_bimodal(lo):.2f}  mean BC={np.mean([r['bc'] for r in lo]):.3f}")
json.dump(recs,open("experiments/ert/aita_topic_stats.json","w"),indent=2)
print("\nwrote experiments/ert/aita_topic_stats.json")
