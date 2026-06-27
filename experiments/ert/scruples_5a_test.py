#!/usr/bin/env python3
"""ERT Falsifier 5a (PRIMARY) on Scruples Anecdotes. Moral position is measured from
REAL community votes: p_wrong = WRONG/(RIGHT+WRONG) per anecdote (fixes AITA's weak
text-probe). Cluster anecdotes by situation type; ERT predicts contested types have a
BIFURCATED judgment (two camps near 0 and 1 -> a split reference) beyond mere dispersion,
not a unimodal spread. The partial correlation (bimodality | dispersion) is the test.
Nulls reported honestly."""
import numpy as np, json, sys, os, glob
sys.path.insert(0,"experiments/ert"); import ert_analysis as E
from scipy.stats import spearmanr, rankdata
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans

rows=[]
for f in glob.glob("experiments/ert/scruples_data/anecdotes/*train*.jsonl"):
    for line in open(f,encoding="utf-8"):
        r=json.loads(line); b=r.get("binarized_label_scores") or {}
        tot=b.get("RIGHT",0)+b.get("WRONG",0)
        if tot<3: continue                      # need a minimum of votes
        txt=((r.get("title") or "")+". "+(r.get("text") or "")[:1200]).strip()
        if len(txt)<20: continue
        rows.append((txt, b["WRONG"]/tot, tot))
texts=[r[0] for r in rows]; pwrong=np.array([r[1] for r in rows]); votes=np.array([r[2] for r in rows])
print(f"anecdotes (>=3 votes): {len(rows)}   mean votes/anecdote: {votes.mean():.1f}  median: {int(np.median(votes))}")
def bent(p): 
    p=np.clip(p,1e-9,1-1e-9); return -(p*np.log2(p)+(1-p)*np.log2(1-p))
print(f"individually divisive anecdotes (binary entropy>0.8): {(bent(pwrong)>0.8).mean()*100:.0f}%")

MODEL=os.environ.get("ERT_EMB","sentence-transformers/all-MiniLM-L6-v2")
cache=f"experiments/ert/scruples_emb_{MODEL.split(chr(47))[-1]}.npy"
if os.path.exists(cache): emb=np.load(cache)
else:
    from sentence_transformers import SentenceTransformer
    m=SentenceTransformer(MODEL)
    emb=m.encode(texts,normalize_embeddings=True,batch_size=64,show_progress_bar=True)
    np.save(cache,emb)
print("emb:",emb.shape)

K=40; lab=KMeans(K,n_init=4,random_state=0).fit_predict(emb)
def dbic1d(x):
    x=x.reshape(-1,1)
    return GaussianMixture(1,random_state=0).fit(x).bic(x)-GaussianMixture(2,n_init=4,random_state=0).fit(x).bic(x)
recs=[]
for c in range(K):
    idx=np.where(lab==c)[0]
    if len(idx)<25: continue
    pw=pwrong[idx]
    recs.append(dict(n=int(len(idx)),disp=float(pw.std()),dbic=float(dbic1d(pw)),
                     contest=float(np.mean(bent(pw)>0.8)), meanpw=float(pw.mean())))
print(f"\nusable situation-type clusters: {len(recs)}")
disp=np.array([r["disp"] for r in recs]); db=np.array([r["dbic"] for r in recs]); con=np.array([r["contest"] for r in recs])
def sp(a,b,l):
    rho,p=spearmanr(a,b); print(f"  {l:40s} rho={rho:+.3f} p={p:.4g}")
print("== ERT 5a (real-vote axis): two-camp bifurcation ==")
sp(disp,db,"judgment dispersion vs dBIC (bimodality)")
sp(con,db,"contestation (frac divisive) vs dBIC")
A=rankdata(disp); B=rankdata(db); resid=B-np.polyval(np.polyfit(A,B,1),A)
rho,p=spearmanr(rankdata(con),resid)
print(f"  partial (contestation vs bimodality | dispersion)  rho={rho:+.3f} p={p:.4g}")
print(f"  clusters bimodal (dBIC>10): {int((db>10).sum())}/{len(recs)}")
json.dump(recs,open("experiments/ert/scruples_5a_stats.json","w"),indent=2)
print("wrote experiments/ert/scruples_5a_stats.json")
