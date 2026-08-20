/-
Machine-checked confirmations for "The Legal Bond Index" (JSciLaw),
supplementary to the Zenodo archive (concept DOI 10.5281/zenodo.21310251).

Two kernel-checked facts:

1. `confusion_rate_identity` — the arithmetic identity linking the
   false-positive rate to prevalence, positive predictive value, and the
   false-negative rate on any confusion matrix with nondegenerate margins:

      FPR = (p / (1 - p)) * ((1 - PPV) / PPV) * (1 - FNR)

   This is the algebra underlying the Chouldechova (2017) impossibility
   discussed in the paper's §2: the identity forces error-rate imbalance
   whenever predictive parity holds and prevalence differs.

2. `impossibility_of_parity` — the corollary in impossibility form: two
   groups with equal PPV, equal FNR, and different prevalence must have
   different FPRs (all quantities in the open unit interval).

Scope note: these are checks of the arithmetic the paper cites, not a
formalization of the cited papers; the LBI estimator itself is empirical
and is verified by the archived pipeline, not by proof.
-/
import Mathlib

namespace LBI

/-- Confusion-matrix data with nondegenerate margins: true/false
positives/negatives as positive reals. -/
structure Confusion where
  tp : ℝ
  fp : ℝ
  tn : ℝ
  fn : ℝ
  tp_pos : 0 < tp
  fp_pos : 0 < fp
  tn_pos : 0 < tn
  fn_pos : 0 < fn

namespace Confusion

variable (c : Confusion)

noncomputable def n : ℝ := c.tp + c.fp + c.tn + c.fn
noncomputable def prevalence : ℝ := (c.tp + c.fn) / c.n
noncomputable def ppv : ℝ := c.tp / (c.tp + c.fp)
noncomputable def fnr : ℝ := c.fn / (c.tp + c.fn)
noncomputable def fpr : ℝ := c.fp / (c.fp + c.tn)

lemma n_pos : 0 < c.n := by
  unfold n; nlinarith [c.tp_pos, c.fp_pos, c.tn_pos, c.fn_pos]

lemma pos_margin_pos : 0 < c.tp + c.fn := by nlinarith [c.tp_pos, c.fn_pos]
lemma neg_margin_pos : 0 < c.fp + c.tn := by nlinarith [c.fp_pos, c.tn_pos]
lemma pred_pos_pos : 0 < c.tp + c.fp := by nlinarith [c.tp_pos, c.fp_pos]

lemma one_sub_prevalence : 1 - c.prevalence = (c.fp + c.tn) / c.n := by
  have hn : c.tp + c.fp + c.tn + c.fn ≠ 0 := by
    nlinarith [c.tp_pos, c.fp_pos, c.tn_pos, c.fn_pos]
  unfold prevalence n
  field_simp
  ring

/-- The rate identity: FPR = (p/(1-p)) · ((1-PPV)/PPV) · (1-FNR). -/
theorem confusion_rate_identity :
    c.fpr = (c.prevalence / (1 - c.prevalence)) *
            ((1 - c.ppv) / c.ppv) * (1 - c.fnr) := by
  have hn := c.n_pos
  have hpm := c.pos_margin_pos
  have hnm := c.neg_margin_pos
  have hpp := c.pred_pos_pos
  have h1 : 1 - c.prevalence = (c.fp + c.tn) / c.n := c.one_sub_prevalence
  have h2 : 1 - c.ppv = c.fp / (c.tp + c.fp) := by
    unfold ppv
    have hpp' : c.tp + c.fp ≠ 0 := ne_of_gt c.pred_pos_pos
    field_simp
    ring
  have h3 : 1 - c.fnr = c.tp / (c.tp + c.fn) := by
    unfold fnr
    have hpm' : c.tp + c.fn ≠ 0 := ne_of_gt c.pos_margin_pos
    field_simp
    ring
  rw [h1, h2, h3]
  unfold fpr prevalence ppv n
  have hnn : c.tp + c.fp + c.tn + c.fn ≠ 0 := by nlinarith
  have hpm' : c.tp + c.fn ≠ 0 := ne_of_gt hpm
  have hnm' : c.fp + c.tn ≠ 0 := ne_of_gt hnm
  have hpp' : c.tp + c.fp ≠ 0 := ne_of_gt hpp
  have htp' : c.tp ≠ 0 := ne_of_gt c.tp_pos
  field_simp

end Confusion

/-- Impossibility form: with equal PPV, equal FNR, and different
prevalence, the false-positive rates must differ. -/
theorem impossibility_of_parity (c₁ c₂ : Confusion)
    (hppv : c₁.ppv = c₂.ppv) (hfnr : c₁.fnr = c₂.fnr)
    (hprev : c₁.prevalence ≠ c₂.prevalence)
    (hp₁ : c₁.prevalence < 1) (hp₂ : c₂.prevalence < 1)
    (hfnr_lt : c₁.fnr < 1) :
    c₁.fpr ≠ c₂.fpr := by
  have h₁ := c₁.confusion_rate_identity
  have h₂ := c₂.confusion_rate_identity
  intro heq
  -- with shared PPV and FNR, equal FPR forces equal odds p/(1-p),
  -- hence equal prevalence, contradiction.
  have hppv_pos : 0 < c₁.ppv := by
    unfold Confusion.ppv
    exact div_pos c₁.tp_pos c₁.pred_pos_pos
  have hppv_lt : c₁.ppv < 1 := by
    unfold Confusion.ppv
    rw [div_lt_one c₁.pred_pos_pos]
    nlinarith [c₁.fp_pos]
  have hfnr_pos : 0 < 1 - c₁.fnr := by linarith
  have hfac : 0 < (1 - c₁.ppv) / c₁.ppv * (1 - c₁.fnr) := by
    apply mul_pos
    · exact div_pos (by linarith) hppv_pos
    · exact hfnr_pos
  rw [h₁, h₂, ← hppv, ← hfnr] at heq
  set K : ℝ := (1 - c₁.ppv) / c₁.ppv * (1 - c₁.fnr) with hK
  have hKpos : 0 < K := hfac
  have heq' : c₁.prevalence / (1 - c₁.prevalence) * K =
              c₂.prevalence / (1 - c₂.prevalence) * K := by
    calc c₁.prevalence / (1 - c₁.prevalence) * K
        = c₁.prevalence / (1 - c₁.prevalence) *
            ((1 - c₁.ppv) / c₁.ppv) * (1 - c₁.fnr) := by rw [hK]; ring
      _ = c₂.prevalence / (1 - c₂.prevalence) *
            ((1 - c₁.ppv) / c₁.ppv) * (1 - c₁.fnr) := heq
      _ = c₂.prevalence / (1 - c₂.prevalence) * K := by rw [hK]; ring
  have hodds : c₁.prevalence / (1 - c₁.prevalence) =
               c₂.prevalence / (1 - c₂.prevalence) :=
    mul_right_cancel₀ (ne_of_gt hKpos) heq'
  have h1 : 0 < 1 - c₁.prevalence := by linarith
  have h2 : 0 < 1 - c₂.prevalence := by linarith
  have hmono : c₁.prevalence = c₂.prevalence := by
    have hcm : c₁.prevalence * (1 - c₂.prevalence) =
               c₂.prevalence * (1 - c₁.prevalence) := by
      field_simp at hodds
      linarith [hodds]
    nlinarith [hcm]
  exact hprev hmono

end LBI
