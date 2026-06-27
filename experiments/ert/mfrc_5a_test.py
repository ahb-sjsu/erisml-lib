#!/usr/bin/env python3
"""ERT Falsifier 5a on MFRC with a LABELED moral axis (fixes AITA's AUC~0.6 flaw).
Each text carries multiple annotators' moral-foundation labels -> a labeled moral
vector + a direct annotator-disagreement (entropy). Cluster texts by topic; ERT
predicts contested clusters are BIMODAL in moral-foundation space (two annotator
camps / split reference) beyond dispersion. Nulls reported honestly."""
import numpy as np, sys, json, os
from collections import defaultdict, Counter
sys.path.insert(0,"experiments/ert"); import ert_analysis as E
from datasets import load_dataset
from scipy.stats import spearmanr, rankdata, entropy
ds=load_dataset("USC-MOLA-Lab/MFRC",split="train_dedup")

by=defaultdict(list)
meta={}
for r in ds:
    by[r["text"]].append(r["annotation"]); meta[r["text"]]=r["subreddit"]
BASE=["Care","Equality","Proportionality","Loyalty","Authority","Purity","Thin Morality","Non-Moral"]
texts=[t for t,v in by.items() if len(v)>=3]      # >=3 annotators
print(f"texts with >=3 annotators: {len(texts)}")
def fvec(anns):                                   # mean multi-hot over BASE foundations
    rows=[[1.0 if fdn in set(x.strip() for x in a.split(",")) else 0.0 for fdn in BASE] for a in anns]
    return np.array(rows,float).mean(0)
def disagree(anns):                               # mean per-foundation binary entropy (annotator split)
    p=np.clip(fvec(anns),1e-9,1-1e-9)
    return float(np.mean(-(p*np.log2(p)+(1-p)*np.log2(1-p))))
M=np.array([fvec(by[t]) for t in texts])          # 8-dim moral-foundation emphasis per text
disag=np.array([disagree(by[t]) for t in texts])  # annotator disagreement (split over foundations)

cache="experiments/ert/mfrc_emb.npy"
if os.path.exists(cache): emb=np.load(cache)
else:
    from sentence_transformers import SentenceTransformer
    m=SentenceTransformer("BAAI/bge-base-en-v1.5")
    emb=m.encode(texts,normalize_embeddings=True,batch_size=64,show_progress_bar=True)
    np.save(cache,emb)
print("emb:",emb.shape)

from sklearn.cluster import KMeans
K=40; lab=KMeans(K,n_init=4,random_state=0).fit_predict(emb)
recs=[]
for c in range(K):
    idx=np.where(lab==c)[0]
    if len(idx)<25: continue
    V=E.fisher_rao_embed(M[idx])                  # cluster's moral vectors on FR sphere
    disp=E.dispersion(V); sc,_=E.principal_geodesic_scores(V); b=E.bimodality(sc)
    if np.isnan(b["dbic"]): continue
    recs.append(dict(n=int(len(idx)),disagree=float(disag[idx].mean()),
                     disp=float(disp),dbic=float(b["dbic"]),bc=float(b["bc"])))
print(f"\nusable clusters: {len(recs)}")
dg=np.array([r["disagree"] for r in recs]); db=np.array([r["dbic"] for r in recs]); dp=np.array([r["disp"] for r in recs])
def sp(a,b,l):
    rho,p=spearmanr(a,b); print(f"  {l:38s} rho={rho:+.3f} p={p:.4g}")
print("== ERT 5a (labeled axis): contestation -> BIMODALITY ==")
sp(dg,db,"annotator-disagreement vs dBIC")
sp(dg,dp,"annotator-disagreement vs dispersion (ctrl)")
A=rankdata(dp); B=rankdata(db); resid=B-np.polyval(np.polyfit(A,B,1),A)
rho,p=spearmanr(rankdata(dg),resid); print(f"  partial (disagree vs dBIC | dispersion)  rho={rho:+.3f} p={p:.4g}")
print(f"  clusters bimodal (dBIC>10): {int((db>10).sum())}/{len(recs)}")
json.dump(recs,open("experiments/ert/mfrc_5a_stats.json","w"),indent=2)
print("wrote experiments/ert/mfrc_5a_stats.json")
