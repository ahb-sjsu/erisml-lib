# Scoping: a properly-powered polarized-corpus test of ERT

The first real-data probe (AITA, see [`RESULTS.md`](RESULTS.md)) was an **inconclusive null** for three
fixable reasons: (1) the moral axis was barely recoverable (AUC ≈ 0.60); (2) verdicts were 4.5:1 skewed
with no vote margins, so contestation was *inferred* not *measured*; (3) the curvature half of Falsifier 5
was never tested. This document surveys public ethics datasets and designs a test that fixes all three.

## What ERT's falsifiers actually demand

| Falsifier | Needs |
|---|---|
| **5a** schism = *bimodality* (two references), not just high variance | per-item **distributional / vote-margin** labels (measure contestation directly); a **recoverable moral axis**; enough items for a bimodality test |
| **5b** schism concentrates on **high-curvature (sacred/identity)** axes; references **cluster by loads** | **cross-group** response distributions (each group = a load configuration → its own Fréchet neutral); a **direct curvature estimate** |
| **6** **critical slowing-down** (rising variance + autocorrelation) before a schism | a **time series** of a community's reference, ideally many points |

## Survey of public ethics datasets

| Dataset | Size | Label type | Disagreement signal | Cross-group? | Temporal? | Access | Best for |
|---|---|---|---|---|---|---|---|
| **Scruples — Anecdotes** ([AllenAI](https://github.com/allenai/scruples)) | 32k anecdotes / **625k judgments** | **judgment distribution** per anecdote | **direct** (curated to include divisive cases; the paper's own point: "norms are not clean-cut") | no | no | GitHub (CC) | **5a (primary)** |
| **Scruples — Dilemmas** | 10k paired actions | crowd preference distribution | direct | no | no | GitHub | 5a (paired control) |
| **Social Chemistry 101** ([GitHub](https://github.com/mbforbes/social-chemistry-101)) | 292k RoTs (~30k AITA situations) | 12 dims incl. **anticipated agreement** (ordinal: <1%…>90%) + MF + cultural pressure | **direct** (agreement is an annotated axis) | partial (cultural pressure) | no | GitHub (CC BY-SA) | 5a + 5b (curvature↔sacred) |
| **MFTC** ([Hoover 2020](https://journals.sagepub.com/doi/10.1177/1948550619876629)) | 35k tweets, 7 domains | 10 Moral-Foundation labels, **≥3 annotators each** | **annotator-level** | by topic (BLM, Election, MeToo, ALM…) | no | request/GitHub | 5a (labeled axis) + 5b |
| **MFRC** ([HF](https://huggingface.co/datasets/USC-MOLA-Lab/MFRC)) | ~17.9k Reddit comments | MF labels, multi-annotator | annotator-level | by subreddit | no | **HF (easy)** | 5a (labeled axis) |
| **Moral Machine** ([Nature 2018](https://www.nature.com/articles/s41586-018-0637-6)) | **40M decisions, 233 countries** | choice rates per dimension | direct | **yes — 3 cultural clusters** (W/E/S) | no | OSF (large) | **5b (clustering = candidate references)** |
| **GlobalOpinionQA** ([HF](https://huggingface.co/datasets/Anthropic/llm_global_opinions)) | 2,556 Qs | **per-country % distributions**, 100+ nations (Pew GAS + WVS) | direct | **yes (country)** | no | **HF (easy)** | **5b (low-effort)** |
| **World Values Survey** ([WVS](https://www.worldvaluessurvey.org)) | 120+ countries, **waves 1981→2026** | 19 ethical-norm items (−1…1) + many | direct | yes (country) | **yes (5–10 yr waves)** | free (registration) | **6 (only temporal option)** + 5b |
| **ETHICS** (Hendrycks 2021) | ~130k | binary correctness | low (consensus by design) | no | no | GitHub | weak (not polarized) |
| **MIC** (Ziems 2022) | 38k QA + RoT | agreement/violation | moderate | no | no | GitHub | 5a (secondary) |

## Recommended design — three targeted tests

### Primary: Falsifier 5a on Scruples Anecdotes (fixes all three AITA failures)
- **Contestation, measured not inferred:** each anecdote carries a judgment *distribution*; divisiveness = its entropy/normalized dispersion. No skew problem, no topic-clustering proxy.
- **Pipeline:** embed anecdotes (strong encoder **and** the framework's `MoralVector`/DEME scorer for a *labeled* axis, so we're not hostage to AUC ≈ 0.6); place on the moral manifold; for the divisive vs consensus strata, test whether divisive items form a **bimodal** structure (two Fréchet basins) vs a unimodal high-variance blob — GMM 1-vs-2 BIC, Hartigan dip, Sarle BC, **plus** a direct two-basin Fréchet-landscape count (reuse `synthetic_bifurcation.py`'s minima finder).
- **Confirms ERT if:** divisiveness tracks *bimodality* beyond dispersion (the partial-correlation that was ≈0 on AITA). **Falsifies if:** divisive items are reliably unimodal-just-wider — disagreement without bifurcation.

### Secondary: Falsifier 5b on GlobalOpinionQA (+ Moral Machine confirm)
- Each **country = a load configuration**; compute its reference (Fréchet mean of its response distribution in the question-embedding space). **ERT predicts the per-country neutrals cluster** (similar loads → nearby neutrals) and that the questions where countries split into *multiple* reference-clusters are the **high-curvature sacred/identity axes** (religion, sexuality, national belonging), not the tradeable (economic) ones.
- **Direct curvature test:** estimate local sectional curvature on the question-embedding manifold (geodesic-vs-chordal ratios / triangle comparison, calibrated against the synthetic harness); correlate curvature with cross-country multi-modality. Moral Machine's **three empirical clusters** are an independent check that reference-bifurcation across cultures is real.

### Exploratory: Falsifier 6 on WVS waves
- For each country×item, build the reference time series across waves (1981→2024). On societies that demonstrably **polarized** on an item, test for **critical slowing-down** (rising lag-1 autocorrelation + variance) before the split, absent in matched non-splitting controls.
- **Honest limit:** 5–10-yr spacing gives few points — this is qualitative/suggestive at best. A finer-grained supplement (one subreddit's reference over months) trades temporal resolution for weaker schism ground-truth.

## Confounds to pre-empt (and how)
- **Embedding instrument** still mediates (the standing §6 caveat). Mitigate: prefer **labeled** axes (MF in MFTC/MFRC; the `MoralVector` scorer) over latent probes; report **cross-encoder robustness** (as we did on AITA).
- **Curvature estimation is method-dependent and noisy.** Mitigate: ≥2 estimators + **calibrate on the synthetic sphere/plane/hyperbolic harness** where curvature is known.
- **Bimodality ≠ schism** unless sub-populations actually occupy the basins. Where annotator/country identity exists (MFTC, GlobalOpinionQA), check the basins map to *groups*, not artifacts.
- **Multiple comparisons** across items/axes — pre-register the sacred-vs-tradeable contrast; correct.

## Prioritized plan (effort → value)
1. **GlobalOpinionQA** — trivial HF access, small; quickest 5b (per-country neutral clustering + curvature). *Do first.*
2. **Scruples Anecdotes** — the primary 5a test; moderate prep; the direct fix for the AITA null.
3. **WVS Wave-7 + back-waves** — 5b cross-cultural + the only shot at Falsifier 6.
4. **Moral Machine** — heavy (40M rows) but the strongest independent confirmation of cross-cultural reference clustering.

MFTC/MFRC are the fallback if a *labeled* moral axis is needed to beat the AUC ≈ 0.6 ceiling.
