# RQ1 mechanics run — unsealed, 2026-08-27

Not a sealed result. This is the shakedown that must pass **before**
`PREREG.md` freezes anything: it shows the gate suite runs, that the
vector set can distinguish right from wrong, and where the vector set
is thin. Doctrinal content remains unverified (`CONSTRAINT-SUITE.md`
§7), so nothing here is a claim about *Loomis* or about COMPAS.

## (a) Vector set

`python run_vectors.py` → **31/31 exact match**, ad-hoc-logic scan
**CLEAN** (no case, vector, or defendant identifier inside
`DoctrinalProjection`'s source). E1's candidate bar is met on
mechanics.

## (b) Mutation gate — does the suite have teeth?

A suite written by the same hand as the code it tests passes on the
first run by construction; that is evidence of nothing. Five
deliberate mutations, each asserted to be caught
(`python mutation_check.py`):

| mutation | what it breaks | caught by | survivors |
|---|---|---|---|
| M1 undetermined-as-compliant | silence reads as compliance | 15 vectors | 16/31 |
| M2 missing-fields-pass | absent fields return a clean pass | 17 vectors | 14/31 |
| M3 attribute-policy-hard-coded | doctrine baked into code, not read from the profile | **V-J2 only** | 30/31 |
| M4 severity-inflation | moderate failure escalated to grave | V-F4, V-C2 | 29/31 |
| M5 determinative-over-fires | any score mention counts as determinative | 20 vectors | 11/31 |

**5/5 caught; restored logic reproduces 31/31 exactly.**

## What the margins say (the useful part)

- **M3 was caught by exactly one vector.** The profile-swap pair is
  the *entire* defence against doctrine being hard-coded into the gate
  logic — the specific failure the "no ad-hoc logic" claim is about.
  One vector is too thin a margin for a load-bearing claim.
  **Pre-seal action:** add profile-swap coverage for at least three
  more gates (D1 warning sets, D5 sanctioned decision points, D4
  validation requirement), so every profile-parameterized gate has a
  swap test rather than only D7.
- **M4 was caught by two vectors**, both involving D4 — the only
  `moderate`-severity gate, so severity roll-up is tested on a single
  gate. **Pre-seal action:** consider a second moderate gate or an
  explicit roll-up unit test.
- M1/M2/M5 are caught broadly, as they should be: they break the
  undetermined semantics and the over-firing guard, which most
  vectors touch.

## Reproduce

```
PYTHONPATH=<path-to>/erisml-compiler/src python run_vectors.py
PYTHONPATH=<path-to>/erisml-compiler/src python mutation_check.py
```

Artifacts: `vector_results.json`, `mutation_results.json`.

## Still open before any seal

1. ⧗ doctrine quote-verification against 881 N.W.2d 749 (pin cites).
2. Legal review of the encodings.
3. The two vector-coverage actions above.
4. E4 (auditability gap) is *predicted* at 4/7 but not yet measured;
   measuring it needs the COMPAS records mapped into `DecisionRecord`,
   which is the next code step.
