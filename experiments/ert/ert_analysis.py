"""Shared ERT analysis primitives, calibrated against synthetic_bifurcation.py.
Geometry: distributions live on the Fisher-Rao sphere via p -> sqrt(p) (unit sphere,
geodesic = 2*Bhattacharyya angle). Text embeddings use Euclidean/cosine geometry."""
import numpy as np
from sklearn.mixture import GaussianMixture

def sph_dist(x, Y):                      # geodesic distance on unit sphere
    return np.arccos(np.clip(Y @ x, -1, 1))

def frechet_sphere(V, w=None, iters=400, lr=0.4):
    """Weighted Frechet (Karcher) mean on the unit sphere by tangent-space GD."""
    w = np.ones(len(V)) if w is None else np.asarray(w, float); w = w/w.sum()
    x = (w[:,None]*V).sum(0); x = x/np.linalg.norm(x)
    for _ in range(iters):
        d = sph_dist(x, V)
        with np.errstate(invalid="ignore", divide="ignore"):
            coef = np.where(d>1e-9, d/np.sin(d), 1.0)
        log = coef[:,None]*(V - np.outer(np.cos(d), x))    # log_x(V_i)
        step = (w[:,None]*log).sum(0)
        x = np.cos(np.linalg.norm(step)*lr)*x + np.sin(np.linalg.norm(step)*lr)*(step/ (np.linalg.norm(step)+1e-12))
        x = x/np.linalg.norm(x)
    return x

def principal_geodesic_scores(V, mean=None):
    """1-D scores: log-map to tangent at Frechet mean, PCA, first component."""
    m = frechet_sphere(V) if mean is None else mean
    d = sph_dist(m, V)
    with np.errstate(invalid="ignore", divide="ignore"):
        coef = np.where(d>1e-9, d/np.sin(d), 1.0)
    T = coef[:,None]*(V - np.outer(np.cos(d), m))          # tangent vectors
    T = T - (T@m)[:,None]*m                                # ensure tangent
    U,S,Wt = np.linalg.svd(T - T.mean(0), full_matrices=False)
    return (T - T.mean(0)) @ Wt[0], d                      # scores, geodesic radii

def dispersion(V, mean=None):
    m = frechet_sphere(V) if mean is None else mean
    return float(np.mean(sph_dist(m, V)**2))

def bimodality(x):
    """Battery on 1-D scores. Returns dBIC(>0=>2 comps), Sarle BC(>0.555 bimodal),
    dip (Hartigan), and a silhouette-style 2-cluster separation."""
    x = np.asarray(x, float); n = len(x); out = {}
    if n < 12: return dict(dbic=np.nan, bc=np.nan, dip=np.nan, sep=np.nan, n=n)
    xr = x.reshape(-1,1)
    b1 = GaussianMixture(1, random_state=0).fit(xr).bic(xr)
    b2 = GaussianMixture(2, n_init=4, random_state=0).fit(xr).bic(xr)
    out["dbic"] = float(b1-b2)
    s = ((x-x.mean())**3).mean()/x.std()**3
    k = ((x-x.mean())**4).mean()/x.std()**4
    out["bc"] = float((s**2+1)/(k+3*(n-1)**2/((n-2)*(n-3))))
    out["dip"] = float(_dip(x))
    # 2-means separation: gap between sorted halves' means / pooled std
    xs=np.sort(x); g=GaussianMixture(2,n_init=4,random_state=0).fit(xr)
    mu=np.sort(g.means_.ravel()); out["sep"]=float((mu[1]-mu[0])/(x.std()+1e-9))
    out["n"]=n
    return out

def _dip(x):
    """Hartigan dip statistic (simple O(n log n) implementation)."""
    x=np.sort(np.asarray(x,float)); n=len(x)
    if n<4: return np.nan
    cdf=np.arange(1,n+1)/n
    # greatest convex minorant / least concave majorant distance to ecdf
    def gcm(y):
        m=len(y); h=[0]; 
        for i in range(1,m):
            while len(h)>=2 and (y[i]-y[h[-1]])/(i-h[-1]) <= (y[h[-1]]-y[h[-2]])/(h[-1]-h[-2]):
                h.pop()
            h.append(i)
        f=np.interp(np.arange(m),h,[y[j] for j in h]); return f
    lo=gcm(cdf); hi=-gcm(-cdf[::-1])[::-1]
    return float(np.max(np.abs(cdf-lo)).clip(0)+0)  # dip proxy (max ecdf-gcm gap)

def fisher_rao_embed(P):                 # rows: probability vectors -> unit sphere
    P=np.clip(np.asarray(P,float),0,None); P=P/P.sum(1,keepdims=True)
    return np.sqrt(P)
