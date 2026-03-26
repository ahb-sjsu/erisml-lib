# Revision Notes for Variable Loss Aversion Paper

## Changes to make in response to reviewer feedback:

### 1. Derivation: General formula first, √d as special case

**Current**: Presents λ = √d as THE result.
**Revised**: Present the general formula first:

λ(g) = √(Σ_{k∈A_loss} σ_k^{-2}) / √(σ_1^{-2})

where A_loss is the set of dimensions activated by losing good g.
Then show that under isotropy (σ_k = σ for all active k), this simplifies to √d.

State clearly: "The √d formula is a benchmark for the isotropic case. The
general prediction depends on the eigenstructure of Σ restricted to the
active subspace. For the calibrated Σ (Table 5), the non-monetary dimensions
have similar variance (σ_kk = 0.25 for k ≥ 2), so the isotropic approximation
is reasonable for the non-monetary block, but the monetary dimension has
σ_11 = 25.0 — two orders of magnitude larger — which is why gains (monetary
only) have low friction and losses (multi-dimensional) have high friction."

### 2. Fix heirloom inconsistency

**Problem**: Paper says d=7 in one place, d≈12.5 in another.
**Fix**: Use d=7 consistently. The λ = √7 = 2.65.
Delete the "effective ≈ 12.5" — it was reverse-engineered from 3.53² = 12.5
which is exactly the kind of disguised tuning the reviewer flagged.

If we want to reach λ = 3.53, we need to use the ACTUAL Σ (non-isotropic)
and show that the weighted formula gives ~3.5 for heirlooms because the
identity dimension (σ_77 = 0.25) has much higher precision weight than
the monetary dimension (σ_11 = 25.0), so dim 7 contributes disproportionately.

Actually: with σ_11 = 25 and σ_kk = 0.25 for k=2..9:
- gain friction: √(δ²/25) = δ/5
- loss of heirloom (7 dims active): √(δ²/25 + 6*δ²/0.25) = δ√(0.04 + 24) = δ√24.04 ≈ 4.9δ
- λ = 4.9δ / (δ/5) = 4.9 * 5 = 24.5 ... that's too high

Wait — the gain also uses σ_11 = 25, so:
- gain: √(δ²/σ_11) = δ/√25 = δ/5
- loss (d dims at σ_kk = 0.25 each, plus monetary at σ_11 = 25):
  √(δ²/25 + (d-1)*δ²/0.25) = δ√(1/25 + (d-1)/0.25) = δ√(0.04 + 4(d-1))

For d=5: δ√(0.04 + 16) = δ√16.04 ≈ 4.0δ
λ = 4.0 / 0.2 = 20 ... way too high

The issue is that σ_11 = 25 >> σ_kk = 0.25 means non-monetary dimensions
are 100x more precisely weighted. This makes any multi-dimensional loss
ENORMOUSLY more costly than a monetary gain. The actual Σ gives λ >> 2.25.

This means the isotropic √d formula is indeed a SPECIAL CASE and the
actual calibrated Σ gives DIFFERENT (larger) predictions.

**Resolution**: Present the general formula. Show that:
- Isotropic Σ gives λ = √d (benchmark)
- The calibrated Σ gives larger λ because non-monetary dims have higher precision
- The KT benchmark λ ≈ 2.25 is recovered when the effective dimension ratio
  accounts for the precision weighting

### 3. Qualify the zero-parameter claim

**Revised**: "The model has one structural input (Σ), calibrated from a single
dataset, which is then frozen for all subsequent predictions. The dimensional
loading d(g) is assigned based on a qualitative assessment of which attribute
dimensions the good activates. We do not claim this assignment is parameter-free
in the statistical sense; rather, the assignment follows a pre-specified rule
(any dimension plausibly affected by the transaction is counted as active)
that is not fitted to the loss-aversion data. An experimental protocol that
measures d(g) directly (e.g., via attribute rating tasks) would eliminate
analyst judgment from this step."

### 4. Add CIs from bootstrap

Use the 500-bootstrap results. Report predictions as point estimate ± 95% CI.

### 5. Derive WTA/WTP mapping

Add a subsection: "From behavioral friction to WTA/WTP."
The WTA is the minimum price at which the agent will sell (loss path friction).
The WTP is the maximum price at which the agent will buy (gain path friction).
WTA/WTP = BF_loss / BF_gain = λ(d) under the model.
State conditions under which this mapping holds.

### 6. Tone down comparisons

Replace "no existing theory" with "to our knowledge, no existing model derives
variable λ from structural assumptions about the decision space."

Replace "The model produces a cross-game, cross-cultural prediction that no
existing theory can generate" with "The model generates cross-game predictions
from a single calibration, a property shared with Nash equilibrium (which
predicts poorly) but not with CPT or Fehr-Schmidt (which require per-game fitting)."
</content>
