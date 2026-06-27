#!/usr/bin/env python3
"""ERT Falsifier 5b on GlobalOpinionQA: each country = a load configuration; its
response distribution = its position. Per question, countries live on a Fisher-Rao
sphere (p -> sqrt(p)). ERT predicts contested questions are MULTIMODAL (countries
bifurcate into >=2 reference clusters / a split neutral) beyond mere dispersion, and
that this concentrates on SACRED/identity topics over material/economic ones.
Nulls reported honestly. (The `options` field is malformed in this release, so vector
length is taken from the selection vectors themselves.)"""
import numpy as np, sys, json, re, ast
from collections import Counter
sys.path.insert(0,"experiments/ert"); import ert_analysis as E
from datasets import load_dataset
from scipy.stats import spearmanr, rankdata, mannwhitneyu
ds=load_dataset("Anthropic/llm_global_opinions",split="train")

SACRED=re.compile(r"\b(relig|god|homosexual|gay|lesbian|abortion|moral|marriage|immigr|"
                  r"muslim|christian|jew|faith|tradition|patriot|values|ethic|premarital|divorce)\b",re.I)
MATERIAL=re.compile(r"\b(econom|job|trade|inflation|price|tax|wage|financ|growth|unemploy|"
                    r"income|business|market|currency|cost of living)\b",re.I)

recs=[]
for r in ds:
    sel=r["selections"]
    if isinstance(sel,str):
        try: sel=ast.literal_eval(sel[sel.index('{'):sel.rindex('}')+1])
        except Exception: continue
    vals=[v for v in sel.values() if isinstance(v,(list,tuple))]
    if not vals: continue
    L=Counter(len(v) for v in vals).most_common(1)[0][0]
    if L<2: continue
    rows=[np.array(v,float) for v in vals if len(v)==L and sum(v)>0]
    rows=[p/p.sum() for p in rows]
    if len(rows)<15: continue
    P=np.array(rows); V=E.fisher_rao_embed(P)
    disp=E.dispersion(V); sc,_=E.principal_geodesic_scores(V); b=E.bimodality(sc)
    if np.isnan(b["dbic"]): continue
    q=r["question"]
    topic="sacred" if SACRED.search(q) else ("material" if MATERIAL.search(q) else "other")
    recs.append(dict(n=len(rows),L=L,disp=float(disp),dbic=float(b["dbic"]),
                     bc=float(b["bc"]),sep=float(b["sep"]),topic=topic,src=r["source"]))

print(f"usable questions: {len(recs)}  (>=15 countries each)")
disp=np.array([r["disp"] for r in recs]); dbic=np.array([r["dbic"] for r in recs])
bimod=(dbic>10).astype(int)
print(f"BIMODAL (dBIC>10): {bimod.sum()}/{len(recs)} = {bimod.mean()*100:.0f}%   (a split neutral on this fraction of questions)")

def sp(a,b,l):
    rho,p=spearmanr(a,b); print(f"  {l:36s} rho={rho:+.3f} p={p:.4g}")
print("\n== ERT 5b: contestation tracks MULTIMODALITY ==")
sp(disp,dbic,"dispersion vs dBIC")
A=rankdata(disp); Bk=rankdata(dbic)
resid=Bk-np.polyval(np.polyfit(A,Bk,1),A)

print("\n== sacred vs material vs other ==")
for t in ["sacred","material","other"]:
    g=[i for i,r in enumerate(recs) if recs[i]['topic']==t]
    if not g: continue
    fb=np.mean([1 if recs[i]['dbic']>10 else 0 for i in g])
    print(f"  {t:9s} n={len(g):4d}  frac bimodal={fb:.2f}  mean dBIC={np.mean([recs[i]['dbic'] for i in g]):+8.1f}"
          f"  mean disp={np.mean([recs[i]['disp'] for i in g]):.3f}  resid-dBIC={np.mean([resid[i] for i in g]):+.1f}")
si=[i for i,r in enumerate(recs) if r['topic']=='sacred']; mi=[i for i,r in enumerate(recs) if r['topic']=='material']
if si and mi:
    _,p=mannwhitneyu([recs[i]['dbic'] for i in si],[recs[i]['dbic'] for i in mi],alternative="greater")
    print(f"\n  Mann-Whitney sacred dBIC > material : p={p:.4g}")
    _,p2=mannwhitneyu([resid[i] for i in si],[resid[i] for i in mi],alternative="greater")
    print(f"  Mann-Whitney sacred > material, dispersion-controlled (resid) : p={p2:.4g}")
json.dump(recs,open("experiments/ert/goqa_5b_stats.json","w"),indent=2)
print("\nwrote experiments/ert/goqa_5b_stats.json")
