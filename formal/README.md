# Formal verification

Machine-checked proofs for ErisML's mathematical claims, in Lean 4 + Mathlib.

## HohfeldV4.lean — the keystone correction, verified

Verifies the July 2026 keystone correction (commit `ea7ee82`) against Mathlib:

1. **Commuting involutions.** The correlative swap `s` (O↔C, L↔N) and deontic
   negation `r²` (O↔L, C↔N) satisfy `s·s = 1`, `r²·r² = 1`, and `s·r² = r²·s`.
2. **V₄, not D₄.** The subgroup of Perm(4) they generate is isomorphic to the
   Klein four-group (`Multiplicative (ZMod 2 × ZMod 2)`) and has exactly
   4 elements (`card_closure_eq_four`), and it is abelian
   (`measured_sector_abelian`).
3. **Quarter-turn exclusion.** The rotation `r` (O→C→L→N→O) is *not* in the
   generated subgroup (`quarter_turn_not_generated`) — D₄ is strictly more
   structure than the demonstrated operations license.
4. **The ambient machinery is genuinely dihedral.** `r⁴ = 1`, `s·r·s = r⁻¹`,
   and `r·s ≠ s·r` — the posited D₄ extension is well-defined and testable.

The position encoding (0 = Obligation, 1 = Claim, 2 = Liberty, 3 = No-claim)
matches `src/erisml/ethics/hohfeld.py`, whose test suite
(`tests/test_hohfeld_d4.py::test_hohfeldian_operations_generate_v4`) checks the
same closure property numerically.

## Checking it

Requires Lean 4 (`elan`) and a Mathlib-enabled project. With a project pinned to
`leanprover/lean4:v4.32.2` and `mathlib v4.32.2`, drop the file in the project
root and run:

```bash
lake env lean HohfeldV4.lean
```

Zero output = all theorems check.

Last verified: 2026-08-17 on Atlas (Ubuntu 24.04), Lean `v4.32.2`,
Mathlib `v4.32.2` — clean compile, no `sorry`, no warnings.
