# MoralVector v2 — an optimal, standards-traceable architecture for DEME 3.0

**Status (2026-07-08).** Grounded in the DEME 3.0 code (`erisml-lib/src/erisml/ethics/`), the
empirical dimensionality work, and a verified EU/NIST/IEEE standards review (§8 sources). Framework
enumerations are primary-source-verified; the substantive-vs-procedural classification and the DEME
mapping are design inferences on those facts.

## 1. Purpose

Define one canonical MoralVector and its mapping into (a) the DEME rank-1..6 MoralTensor and
(b) the governance DAG, such that it simultaneously satisfies **scientists** (a parsimonious,
empirically-grounded basis), **EU / NIST / IEEE** auditors (traceable coverage of their
dimensions), and **engineers** (an implementable `k` axis + policy blocks). The core finding:
this is a **reconciliation-and-crosswalk** job, not a redesign — DEME 3.0 already carries the
structure the standards need.

## 2. The reconciliation problem — three MoralVectors exist

| source | # dims | has privacy / environmental? | has fidelity / externality / repair? |
|---|---|---|---|
| **DEME 3.0** (`erisml-lib/moral_tensor.py`, v3.0.0) | **9** (3×3) | ✅ yes | ❌ no |
| **erisml-compiler** (`ir/schemas.py`) | 10 | ❌ no | ✅ yes |
| **empirical rank test** (used the 10) | 10 | ❌ | ✅ |

These disagree. §3–§4 pick the canonical `k` and place the leftover concepts on the right axes.

## 3. Canonical `k` — DEME 3.0's nine-dimension 3×3 core

DEME's `MORAL_DIMENSION_NAMES` (k = 0..8) is a **3×3 matrix** — the "Nine Dimensions of Ethical
Assessment" — over `{Individual, Relational, Collective}` scope × `{What Matters (values),
Who Decides (deontic), What We Know (epistemic)}` mode:

| scope \ mode | What Matters (values) | Who Decides (deontic) | What We Know (epistemic) |
|---|---|---|---|
| **Individual** | autonomy_respect `(3)` | rights_respect `(1)` | **privacy_protection `(4)`** |
| **Relational** | virtue_care `(6)` | physical_harm/welfare `(0)` | epistemic_quality `(8)` |
| **Collective** | fairness_equity `(2)` | legitimacy_trust `(7)` | **societal_environmental `(5)`** |

**Why this is the right core:** (a) it already contains `privacy_protection` and
`societal_environmental`, the two axes the standards demand that the compiler's 10-dim lacked;
(b) the 3×3 factorization is itself a low-rank structure — two 3-level factors (scope, mode)
generate 9 dims — which is exactly the kind of parsimony the empirical bifactor result argues for
(one general factor + a small number of structured specifics); (c) it is the axis the tensor
engine actually evaluates.

## 4. Where the "extra" concepts go (resolving 9-vs-10)

The three dimensions DEME "drops" are not lost — they are **structure on other tensor axes**, not
new `k` dimensions:

| compiler-10 concept | belongs on | rationale |
|---|---|---|
| `third_party_externality` | **`n` (party) axis** | harm *distributed across non-consenting parties* = variation in `n`, read off the per-party tensor, not a new value axis |
| `repair_residue` | **`τ` (time) axis** | *residual obligation after* a violation = temporal structure; it is the post-event tail of the `τ` evolution |
| `vow_fidelity` | **deontic column** of `k` | promise/role fidelity is a sub-mode of rights_respect / legitimacy_trust (Who-Decides), not orthogonal |

This is not a workaround — it is more correct. Externality and repair were only ever "extra `k`
dims" because the compiler schema is rank-1 (a flat vector); DEME's higher ranks give them their
natural home.

## 5. The DEME tensor — how the MoralVector plugs in (ranks 1–6)

The MoralVector **is the `k` axis** of `MoralTensor` (`moral_tensor.py`). Higher ranks add context
(`DEFAULT_AXIS_NAMES`):

| rank | shape | adds | what it gives the standards |
|---|---|---|---|
| 1 | `(9,)` | — (V2 MoralVector) | the substantive score |
| 2 | `(9, n)` | parties | EU fundamental-rights impact **per affected person**; `third_party_externality` lives here |
| 3 | `(9, n, τ)` | time | EU post-market monitoring; `repair_residue` = the `τ`-tail |
| 4 | `(9, n, a, c)` | actions × coalitions | alternatives analysis; multi-stakeholder (NIST Map) |
| 5 | `(9, n, τ, s)` | MC samples | **uncertainty quantification** (NIST Measure; EU accuracy/robustness) |
| 6 | `(9, n, τ, a, c, s)` | full context | the complete audit object |

So a change to the MoralVector = a change to the length/ordering/semantics of the `k` axis;
everything downstream (contraction, aggregation, spectral summary) is defined over `k`.

## 6. The governance DAG — Ethics Modules + policy blocks

DEME already implements the **two-layer split** (substantive vs procedural) I would otherwise have
to invent:

- **Ethics Modules** (`EthicsModuleV3`: `em_name`, `stakeholder`, `em_tier`) each **contract the
  tensor along `k`** from a stakeholder/interest perspective — no single EM sees the full tensor.
  `em_tier` orders them into the reflex → tactical → strategic layers (`ethics/layers/`), forming
  the evaluation DAG. A Safety EM contracts `k` with an interest vector weighted on
  `physical_harm`; a Privacy EM on `privacy_protection`; etc.
- **Policy blocks** (`domain/em_profile.py`): `safety, autonomy, fairness, vulnerable_priority,
  privacy, environment, rule_following, **transparency**, **oversight**` + `constraints` +
  `override_policy`, plus per-dimension `dimension_weights`.

The critical classification:
- **Substantive** policy blocks (safety, autonomy, fairness, privacy, environment, vulnerable) →
  each maps to `k` dimension(s) and is realized as an EM contraction.
- **Procedural** policy blocks (**transparency, oversight**, rule_following) → **attestation
  nodes**, NOT tensor contractions. They assert properties of the *system/process*, not scores of
  a scenario. This is the substantive/procedural boundary the frameworks require.

The policy DAG is **rooted in human dignity** (per Geometric Ethics Ch. 19), with the substantive
EMs and procedural attestations as descendants.

## 7. Bifactor ↔ spectral summary ↔ risk tier

The tensor already carries a spectral summary (`attach_spectral_summary` → eigenvalue scalars +
per-axis spectra). This lines up exactly with the empirical result:
- **General factor** (dominant `k`-eigenvalue) = overall moral loading / **severity** → the natural
  driver of the **EU AI Act risk tier** (unacceptable/high/limited/minimal) and NIST measure-
  prioritization.
- **Specific factors** (residual `k`-spectrum) = the structured content, organized by the 3×3
  (scope × mode) factorization.

Empirical grounding (§11): dual-judge scoring of 383 axis-isolated scenarios gave a strong general
factor (eig₁ ≈ 66% of variance) plus ~5 independent residual factors (Horn = 5 after removing the
general factor) and **zero true pairwise redundancy** — i.e. a bifactor structure whose shape the
3×3 core is built to express.

## 8. Standards crosswalk — EU / NIST / IEEE (verified)

Sources (primary, verified 3-0): EU HLEG *Ethics Guidelines for Trustworthy AI* (2019); EU AI Act
Reg. 2024/1689 (Arts 5, 8–15, 17, 27, 50); NIST AI RMF 1.0 (NIST AI 100-1, 2023); IEEE 7000-2021;
IEEE 7010-2020; IEEE EAD1e (2019). The framework **enumerations** are verified facts; the
substantive-vs-procedural **classification** and the DEME **mapping** are design inferences on top
of them. Headline finding, confirmed: the frameworks are **overwhelmingly procedural**; substantive
overlap is narrow (fairness, safety, autonomy, privacy) and DEME 3.0's `k` covers **all four**.

| framework dimension | type | DEME target |
|---|---|---|
| EU HLEG #1 Human agency & oversight | mixed | agency → `k3` autonomy_respect, `k1` rights_respect; oversight → `oversight_policy` (attest) |
| EU HLEG #2 Technical robustness & safety | mixed | safety(content) → `k0` physical_harm; robustness(process) → attest + `s`-axis |
| EU HLEG #3 Privacy & data governance | **substantive** | **`k4` privacy_protection** + `privacy_policy` |
| EU HLEG #4 Transparency | procedural | `transparency_policy` (attest) |
| EU HLEG #5 Diversity, non-discrimination & fairness | **substantive** | `k2` fairness_equity + `fairness_policy` |
| EU HLEG #6 Societal & environmental well-being | **substantive** | **`k5` societal_environmental** + `environment_policy` |
| EU HLEG #7 Accountability | procedural | attest (DAG rooted at human dignity) |
| EU AI Act Art 9 risk management | procedural | GOVERN attest / `constraints` |
| EU AI Act Art 10 data governance | procedural (+`k4`) | `privacy_policy` + data attest |
| EU AI Act Art 11 tech docs / Art 12 logging | procedural | attest; logging ↔ `source_spans` provenance |
| EU AI Act Art 13 transparency | procedural | `transparency_policy` |
| EU AI Act Art 14 human oversight | procedural | `oversight_policy` |
| EU AI Act Art 15 accuracy/robustness/cyber | procedural | attest + `s`-axis (MC uncertainty) |
| **EU AI Act Art 27 FRIA** | **maps to the tensor** | (c) affected persons → **`n` axis**; (d) specific risks of harm → **`k` per party**; (e) oversight → `oversight_policy`; (f) mitigation → `constraints`/`override` |
| NIST valid & reliable | procedural | attest |
| NIST safe | **substantive** | `k0` physical_harm + `safety_policy` |
| NIST secure & resilient | procedural | attest |
| NIST accountable & transparent | procedural | `transparency_policy` + attest |
| NIST explainable & interpretable | procedural | contraction trace + `spectral_summary` + `DimensionScore.explanation`/`source_spans` |
| NIST privacy-enhanced | **substantive** | **`k4` privacy_protection** |
| NIST fair w/ harmful bias managed | **substantive** | `k2` fairness_equity + `fairness_policy` |
| NIST Govern / Map / Measure / Manage | procedural | Measure = tensor eval + `s`-axis; rest = attest |
| IEEE EAD Human Rights | **substantive** | `k1` rights_respect (+ dignity DAG root) |
| IEEE EAD Well-being | **substantive** | `k6` virtue_care + `k5` societal_environmental + `k0` (IEEE 7010's 12 domains) |
| IEEE EAD Data Agency | **substantive** | **`k4` privacy_protection** + `privacy_policy` |
| IEEE EAD Effectiveness / Transparency / Accountability / Awareness-of-Misuse / Competence | procedural | attest / `transparency`, `oversight`, `constraints` |
| IEEE 7000-2021 (process standard) | procedural | *is* the DEME governance process (values → requirements → V&V) |

**The FRIA is the killer app.** EU AI Act **Art 27**'s required content — categories of *affected
persons* × *specific risks of harm*, plus oversight and mitigation — maps *directly* onto a DEME
rank-2+ evaluation (`k`×`n`) plus the oversight/constraint policy blocks. DEME doesn't merely
satisfy the FRIA; the rank-2 tensor **is** the FRIA's computational core. Likewise NIST
"explainable & interpretable" is discharged by the tensor's contraction trace + spectral summary +
per-score `source_spans`/`explanation`, which the engine already emits.

## 9. Gap ledger vs standards (verified)

- **Privacy** — research flags this as the one substantive framework dimension with **no**
  compiler-10 axis (HLEG #3, AI Act Art 10, NIST "privacy-enhanced", EAD "Data Agency").
  **DEME 3.0 already has it: `k4` privacy_protection.** Closed by adopting the DEME-9 core.
- **Environmental / sustainability well-being** — flagged (HLEG #6, IEEE 7010 domain #6
  "Environment"). **DEME 3.0 already has it: `k5` societal_environmental.** Closed. (Note:
  `third_party_externality`, from the compiler-10, is only *adjacent* to environment — not a
  substitute — which is another reason to place it on the `n` axis, §4, and keep `k5` for the
  substantive societal/environmental value.)
- **All other framework dimensions are procedural** (transparency, accountability, oversight,
  robustness, security, logging, risk-management) → covered by DEME's procedural policy blocks +
  attestations + the tensor's explainability affordances. These are **not `k` gaps** — correctly,
  they are properties of the system/process, not moral content of a scenario.
- **Net:** adopting DEME 3.0's 9-dim 3×3 `k` closes **both** substantive standards gaps the
  compiler-10 had. **No new substantive axis is required** for EU + NIST + IEEE coverage.

Caveat: the exact published/draft status of individual IEEE 7000-series sub-standards (7001, 7002,
7003, P7004, P7008, P7014) was **not** reliably verified (a status list was refuted 0-3); only
IEEE **7000-2021** and **7010-2020** are cited here with confidence. Re-verify per-standard on IEEE
Xplore before citing the others in a compliance filing.

## 10. Stakeholder-satisfaction matrix

| stakeholder | served by | how |
|---|---|---|
| Scientists | §3 canonical `k`, §7 bifactor | parsimonious 3×3 basis; empirically grounded; no axis added to please a regulator |
| EU regulators | §7 risk tier, §5 rank-2 parties, §8 crosswalk | severity→tier; per-person rights impact; article-traceable |
| NIST | §5 rank-5 samples, §6 procedural blocks, §8 | uncertainty quantification; Govern/Map/Measure/Manage attestations |
| IEEE | §6 policy DAG, §8 7000-series map | 7000 values→requirements→V&V trace; 7001 transparency block |
| Engineers | §5 `k`/rank API, §6 EM/profile | implementable: MoralVector = `k`; standards = policy blocks + attestations |

## 11. Empirical grounding

Effective-rank analysis (`xbse/experiments/rank_test.py`) across three matrices: MFRC co-mention
(PR 5.78, independence-biased), Moral-Stories valence (PR 2.92), and a 383-scenario axis-isolated
dual-judge matrix (PR 2.24 full → **PR 7.44 / Horn 5 after removing the general factor**, zero
residual redundancy). Conclusion: **bifactor — one general severity factor + ~5 independent
specifics ⇒ minimal basis ≈ 6**, consistent with the 3×3 core (which the general factor + the two
3-level factors span). The number is soft (judge agreement 0.556; `autonomy`/`repair` lacked
isolating data) but the *structure* is robust.

## 12. Open items

1. Reconcile the compiler-10 schema to the DEME-9 `k` in code (move externality→`n`, repair→`τ`,
   fold vow_fidelity into the deontic column); or document the compiler-10 as a rank-1 legacy view
   of the DEME-9 core.
2. Implement the two-layer emit: substantive `k`-contractions (EMs) vs procedural attestations
   (transparency/oversight policy blocks) — and wire the Art 27 FRIA export off the rank-2 tensor.
3. Sharpen the empirical "~5" with a third judge + isolating data for `autonomy_consent` /
   `repair_residue`, then re-run `rank_test` and confirm the residual factor count.
4. Confirm the proportionality/desert axis question (MFT-2.0) against the 3×3 (fairness_equity may
   need an equality/proportionality split — but that would break the clean 3×3 factorization).
5. Re-verify per-standard IEEE 7000-series publication status on IEEE Xplore before any compliance
   filing (see §9 caveat).
