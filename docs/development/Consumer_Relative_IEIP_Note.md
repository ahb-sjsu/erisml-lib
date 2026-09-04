# Consumer-Relative I-EIP: Measured Evidence and Four Proposed Upgrades

**Status:** Evidence note, 2026-09-01. Input to the I-EIP Monitor program
(`docs/I-EIP_Monitor_Whitepaper.md` v1.0; `docs/development/I-EIP_Monitor_Sprint_Plan.md`).
Shakedown-level evidence — two exploratory cells on one small model. Nothing here
changes the sprint plan by itself; each proposal names the follow-up that would seal it.

**Evidence home:** `observation-theory-campaigns` branch `campaign/consumer-relative-ann`,
`analysis/cr-ieip/` (cells `cr_ieip_cell.py`, `cr_ieip_v2.py`; results committed; commits
`1332f8d`, `8a75a23`).

---

## 1. The claim

The §16 criterion grades internal equivariance in the raw L2 norm of the activation
space: `‖h_ℓ(g·x) − ρ_ℓ(g)·h_ℓ(x)‖`. Observation Theory's objection: layer ℓ's
activations have a *consumer* — the downstream network and the EM evaluators — and the
norm that matters is the consumer's read of the residual, not its raw magnitude. A
raw-L2 gate can therefore fail in both directions:

- **False alarm** — a large residual confined to subspaces the downstream computation
  is insensitive to trips the gate for nothing (alert fatigue, needless vetoes).
- **False clear** — a small residual concentrated exactly where downstream reads
  passes the gate. This is the spec-gaming case §1.2 of the whitepaper exists to
  catch, certified as equivariant by the monitor's own metric.

This is the same dissociation measured elsewhere in the OT program (a CSI autoencoder
that wins reconstruction while its consumer false-clears; 0.995-cosine KV keys at
~1e4 perplexity), relocated to a safety monitor.

## 2. What was measured

Two cells, Qwen2.5-0.5B (CPU), g = backtranslation paraphrase over Social-Chemistry
actions, ρ̂ per layer by the whitepaper's own ridge-Procrustes estimator, ground truth =
the model's actual next-token KL between x and g·x.

**v1 (shakedown, 600 pairs, linear-proxy consumer):** raw and consumer-weighted errors
tied globally; the consumer weighting false-cleared fewer behavior-changing cases at
matched flag rates at 3/4 layers (~11 pp). Suggestive only — ρ̂ was underdetermined
(n_cal 360 < d 896).

**v2 (decisive at shakedown level, 2,312 pairs, n_cal 1,387 > d 896, held-out ρ̂ R²
reported; TRUE consumer read — the residual e is injected at layer ℓ by last-position
activation patch and the network's own output-KL response is the metric):**

| layer | ρ̂ R² cal→eval | Spearman raw | Spearman consumer | false-clear raw | false-clear consumer |
|---|---|---|---|---|---|
| 6 | 0.815 → 0.473 | 0.473 | 0.373 | 0.593 | 0.542 |
| 12 | 0.809 → 0.500 | 0.519 | **0.648** | 0.574 | **0.384** |
| 18 | 0.835 → 0.422 | 0.532 | **0.678** | 0.556 | **0.347** |
| 24 | 0.883 → **−0.31** | 0.315 | 0.284 | 0.616 | 0.625 |

At the mid layers a monitor actually probes, the consumer read of the residual predicts
real behavioral change substantially better than raw L2 (+0.13/+0.15 Spearman) and cuts
monitor false-clears by 19–21 pp at matched flag rates. The v1 global null is explained:
a linear proxy of the consumer is too weak; the network's own read carries the signal.

**Limits:** one model, one transform family, the consumer read evaluated in x's context;
early layers mixed; unsealed exploratory cells.

## 3. Two calibration findings independent of the claim

These fell out of running the whitepaper's own estimator honestly and stand regardless
of the consumer-metric question:

1. **Final-layer ρ̂ fails to generalize.** Held-out R² = −0.31 despite cal 0.88: final
   representations are the most content-specific and hardest to Procrustes-map across
   paraphrases. A monitor calibrated at the final layer grades against a broken map.
   Recommendation: probe placement (§3.3 Step 1) should avoid the final layer, or the
   spec should flag it.
2. **Calibration must be validated held-out.** Even mid-stack, cal→eval R² drops
   0.81 → 0.47, and at small corpora (n_cal < d) the ridge estimator near-interpolates
   (v1 measured cal R² 0.92–1.0 at n=360, d=896). Recommendation: §3.3 Step 2 should
   require n_cal ≫ d and a held-out ρ̂ R² floor as an admission criterion for a probe
   layer; a layer whose ρ̂ does not generalize cannot carry an equivariance verdict.

## 4. Four proposed upgrades (each with its sealing path)

1. **Consumer-weighted gating metric.** Grade the §16 residual per layer in the
   consumer norm — either the measured patch-response (inject e, read the output/EM
   response; what v2 did) or `‖e‖_{P_C}` with `P_C = JᵀJ` of the downstream map, and
   per-EM: each EM evaluator supplies its own read operator, giving per-EM thresholds.
   This is consistent with the whitepaper's Reward-Irrecoverability commitment (no
   scalar collapse) and gives the retained tensor structure operational meaning.
   *Seal:* replicate v2 on a second model + a second transform family, prereg'd bars.
   *Status 2026-09-02:* both replications have now been run exploratory-grade and
   CONFIRM v2 — TinyLlama-1.1B (Spearman true 0.654/0.778 vs raw 0.598/0.686,
   false-clear −16/−15 pp, layers 11/16) and fr backtranslation on Qwen2.5-0.5B
   (0.525/0.579 vs 0.432/0.458, −15/−17 pp, layers 12/18); the final-layer ρ̂
   held-out collapse appears in all three runs. Records:
   observation-theory-campaigns `analysis/cr-ieip/cr_ieip_{tl,fr}_result.json`.
   The remaining seal step is the prereg'd bars themselves.
   *Status 2026-09-04, GRADED under seal (PREREG-CR-IEIP v1.0): family FAIL,
   and the failure is the sharpest spec input yet.* The backtranslation cell
   passed (-14/-15pp false-clears at matched flag rates, 1.5B); BOTH
   paraphrase cells (0.5B and 1.5B) INVERTED (+35..+57pp worse than raw)
   with rho's held-out R2 <= 0.00 -- patch-response gating below the rho
   floor is worse than the raw metric it replaces. **Spec rule this
   mandates: gate the consumer-metric path on a mechanical calibration-only
   rho held-out check (measured safe margin: in-regime >= 0.074 vs
   out-of-regime <= -0.0003; the V2 prereg freezes 0.05); below the floor,
   fall back to raw or abstain.** Records: observation-theory-campaigns
   analysis/cr-ieip/ (RESULTS-CR-IEIP.md, cells A/B/C, PREREG-CR-IEIP-V2).
2. **A shipped, measured monitor false-clear rate.** Nominal accept = gate cleared;
   consumer_ok = behavior/EM verdict actually invariant. P(behavior changed | cleared)
   is the honest worth of the monitor and belongs beside its other calibration
   numbers. *Seal:* part of the same prereg; the statistic already exists in the
   OT tooling (turboquant `false_clear`).
3. **ρ̂ freshness.** ρ̂ is a calibration certificate that ages: fine-tunes, LoRAs, and
   distribution shift stale it, and equivariance graded against a stale ρ̂ is a stale
   verdict. The OT-14 refresh-floor law gives the quantitative form; Sprint 2.5's
   drift detection is the hook. *Seal:* a staleness cell (age ρ̂ across a fine-tune,
   measure false-clear vs age).
4. **Validity, not just provenance, in the attestation.** The ECDSA/Merkle artifact
   certifies that the gate ran and what it read; it cannot certify that ρ̂ was fresh,
   thresholds calibrated, and the metric consumer-sound. The attestation should carry
   a validity block — ρ̂ age and held-out R², threshold provenance, which metric
   (raw vs consumer) was used — re-evaluated at use time (the IEEE P3787 pattern; see
   also the provenance-is-not-validity argument in the POSO critique,
   observation-theory-campaigns `paper/poso-provenance-validity/`).

## 5. What this note does not claim

No change to the sprint plan's scope or estimates is requested on this evidence. The
cells are unsealed, single-model, single-transform. The concrete asks are small:
adopt §3's two calibration requirements (cheap, independent of the consumer-metric
question), and schedule the sealing experiments for §4.1–4.2 before the gating
semantics of Sprint 2.5+ freeze — because if the consumer-metric result holds, it
changes what the gate should compute, and that is cheaper to decide before the
enforcement half is built.
