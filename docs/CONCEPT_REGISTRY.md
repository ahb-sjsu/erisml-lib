# Concept Registry — canonical terms across the ethics stack

**Purpose:** one authoritative definition per load-bearing concept, its epistemic
status, and its aliases across the repos (`erisml-lib`, `erisml-compiler`, `xbse`,
`moral-spectrum-analyzer`, `lebse`, and the OT program in
`observation-theory-campaigns` / `turboquant-pro`). Other documents **point here**
rather than restating definitions; a restated definition is where drift starts.
Complements `docs/guides/SQND_ROSETTA_STONE_PRIMER.md` (a physics-to-engineering
translation), which this registry does not duplicate.

**Registry discipline**
1. Every concept has exactly one authoritative source (a file, a proof, or a
   published number). Everything else links.
2. Claims carry their epistemic status inline: **measured / proved**,
   **posited (testable)**, **proposed**, or **retired**. A posited claim may not
   be stated as fact anywhere.
3. Aliases are listed, not eliminated — each repo keeps its natural vocabulary,
   but the registry says which words are the same thing.

Maintained: 2026-09-01. Items marked **[owner]** need the owner's canonization.

---

## 1. Hohfeldian gauge structure — "V4 measured, D4 posited"

**Authoritative:** `formal/HohfeldV4.lean` (machine-checked, Lean 4 + Mathlib,
last verified 2026-08-17) + the header of `src/erisml/ethics/hohfeld.py`;
keystone correction commit `ea7ee82` (July 2026).

**Canonical statement.** The two demonstrated Hohfeldian operations — the
correlative swap `s` (O↔C, L↔N) and deontic negation `r²` (O↔L, C↔N) — are
commuting involutions and generate the **Klein four-group V₄** (abelian,
order 4). **D₄** (order 8, non-abelian; some algebra texts call this group
"D8") is the **posited** ambient group: licensed only if a quarter-turn
(`r`: O→C→L→N→O) is independently demonstrated as a normative operation, which
has not been done. The Lean proof establishes both halves: V₄ closure and
quarter-turn exclusion, and that the ambient D₄ machinery is well-defined and
testable.

**Status:** V₄ **proved/measured**; D₄ **posited (testable)**. Candidate
rehabilitation path (2026-09-01, unsealed): the quarter-turn may correspond to
Hohfeld's *second square* (power/liability/immunity/disability) acting on the
first — power operations are directed and non-involutive; and the group
structure may be **consumer-relative** (visible in a specific readout's metric,
invisible globally) per the OT bridge in §6. Neither is established.

**Known drift (fix list):**
- `src/erisml/ethics/hohfeld.py` module docstring lines 9–12 says "D4 dihedral
  group structure" / "the D4 dihedral group that acts" unqualified, contradicting
  its own file header. (Fixed in the same PR as this registry.)
- `src/erisml/examples/hohfeld_d4_demo.py` intro presents D4 as acting fact.
- `docs/guides/SQND_ROSETTA_STONE_PRIMER.md` §3 headlines "The D₄ Group" and
  leads with non-abelian order-dependence — the posited sector — before the
  measured V₄ appears (§ of `test_hohfeldian_operations_generate_v4`). Needs an
  epistemic-status banner at §3.
- Public-facing SQND material (e.g. `docs/community/linkedin_sqnd_article.md`)
  should be checked for unqualified D4 claims before further sharing. **[owner]**

## 2. The moral dimensions (k-axes)

**Authoritative:** `docs/moralvector_reference.md` — the **9 frozen k-axes**
k0–k8: physical_harm, rights_respect, fairness_equity, autonomy_respect,
privacy_protection, societal_environmental, virtue_care, legitimacy_trust,
epistemic_quality. Signed valence in [−1, +1] with confidence/uncertainty/
direction/spans metadata.

**Alias table (same object, different repos):**
| repo | word |
|---|---|
| erisml-lib / DEME | dimension, k-axis |
| moral-spectrum-analyzer | axis, moral axis |
| xbse | the dimension a **feeder/encoder** targets |
| I-EIP whitepaper | the domain an **EM** (Ethical Module) covers |

**Extensions and dispositions (do not silently merge into the frozen 9):**
- `identity_attack` — a **discovered** axis (MSA), not one of the frozen 9.
  "Nine (+1 discovered)" is the canonical phrasing.
- The MSA 12×12 **specificity gate** assigns per-axis dispositions:
  {care, fairness, legitimacy, epistemic} are **DEMOTE-to-G** (each loses to a
  trained sibling or the general-valence channel on its own held-out pairs);
  the independent axes are **own-axis**. Authoritative: the MSA calibrated-
  authority docs (`docs/CALIBRATED_AUTHORITY.md` in that repo).
- `reliability_weight = max(0, 2·AUROC − 1)` per axis, from xbse's calibration
  block (registered; e.g. physical_harm 0.26, privacy_protection 0.71,
  identity_attack 0.61). One formula, one source (xbse production reports);
  MSA consumes it.
- xbse cross-dataset gate result: **8 of 9 clear**; `rights_respect` **failed
  and is reported failed**. Any doc implying 9/9 validated is wrong.

## 3. The invariance-principle family (EIP / BIP / I-EIP)

Three distinct named principles exist; they must not be used interchangeably:

- **BIP — Bond Invariance Principle** (Bond 2025;
  `docs/guides/bond_invariance_principle.md`): *an ethical judgment is valid
  only if invariant under all bond-preserving transformations* —
  ∀g∈G: 𝒥(T)=𝒥(g·T), where G preserves the bond structure B(T). Scope: the
  judgment function.
- **EIP — Epistemic Invariance Principle** (Geometric Ethics Vol 3 / Geometric
  AI Vol 11): the general invariance principle governing model **I/O behavior**
  under meaning-preserving transformations.
- **I-EIP — Internal EIP** (`docs/I-EIP_Monitor_Whitepaper.md`): the narrowing
  of EIP from behavior to **internal representations**:
  h_ℓ(g·x) ≈ ρ_ℓ(g)·h_ℓ(x), with ρ̂ estimated by regularized Procrustes.

**[owner]** The precise formal relationship between BIP and EIP (identical
principle at different scopes? BIP an instance of EIP over bond-preserving G?)
is stated nowhere; canonize it here once decided.

**Measured caveats on I-EIP calibration (2026-09-01, shakedown evidence;
`docs/development/Consumer_Relative_IEIP_Note.md`):** final-layer ρ̂ fails to
generalize; held-out ρ̂ validation (n_cal ≫ d + an R² floor) should be an
admission criterion for probe layers.

## 4. Validation vocabulary (xbse gate)

**Authoritative:** xbse README + gate code. *Validated* = cleared the shared,
pre-registered cross-dataset adversarial gate; *unvalidated* encoders **cannot**
be used downstream (hard rule); the stub backend is a deterministic
**unvalidated** heuristic for CI only. "Within-dataset AUROC" is explicitly
non-evidence (the correction that reshaped xbse). MSA's trust beats consume
this vocabulary; do not re-define "validated" per-repo.

## 5. Encoder lineage naming

LaBSE (Google, 109-language sentence encoder) → **LeBSE** (legal-domain LaBSE,
`lebse`) → **xbse** (the *-BSE family: small per-dimension moral encoders) →
**MoBSE** (planned purpose-built moral encoder; morality analogue of LaBSE).

**Plan-of-record for MoBSE:** `erisml-compiler/experiments/MOBSE_PLAN.md`
(2026-07-13 post-review checkpoint) **supersedes** `xbse/docs/MOBSE_PLAN.md`
(2026-07-07). The older copy should gain a pointer header. (Found forked
2026-09-01.)

## 6. The OT bridge (Observation Theory ↔ ethics stack)

Terms arriving from `observation-theory-campaigns` / `turboquant-pro` via the
consumer-relative I-EIP work, and their ethics-stack counterparts:

| OT term | definition (authoritative in OT repos) | ethics-stack counterpart |
|---|---|---|
| consumer C | the downstream reader of a representation | the rest of the network; an EM evaluator; a DEME profile |
| read operator P_C | J_Cᵀ J_C, the consumer's local metric | an EM/head's readout map; per-axis probe WᵀW |
| consumer-relative distance | (x−y)ᵀP_C(x−y) | proposed §16 gating norm (Consumer_Relative_IEIP_Note) |
| false clear | nominal certificate accepts; consumer fails | monitor clears but behavior/EM verdict changed |
| provenance vs validity | a signature certifies bytes, not instrument validity | attestation (has) vs validity block (proposed) |
| witnessed certificate | certificate carrying its own in-band verification | attestation + calibration state, re-evaluated at use time |

Epistemic status of the bridge: consumer-weighted equivariance **measured at
shakedown level** on one model (19–21 pp false-clear reduction, mid layers);
replications in flight. Everything in this row-set is **proposed** for the
ethics stack until sealed.

---

*Process note: this registry was created after a 2026-09-01 drift survey. When
adding a concept, add its authoritative source and status; when a claim is
upgraded (posited → measured) or retired, change it HERE first, then let the
repos catch up by pointer.*
