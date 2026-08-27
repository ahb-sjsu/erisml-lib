# RQ1 mechanics run — unsealed, 2026-08-27

Not a sealed result. This is the shakedown that must pass **before**
`PREREG.md` freezes anything: it shows the gate suite runs, that the
vector set can distinguish right from wrong, and where the vector set
is thin. Doctrinal content remains unverified (`CONSTRAINT-SUITE.md`
§7), so nothing here is a claim about *Loomis* or about COMPAS.

## (a) Vector set

`python run_vectors.py` → **37/37 exact match**, ad-hoc-logic scan
**CLEAN** (no case, vector, or defendant identifier inside
`DoctrinalProjection`'s source). E1's candidate bar is met on
mechanics.

## (b) Mutation gate — does the suite have teeth?

A suite written by the same hand as the code it tests passes on the
first run by construction; that is evidence of nothing. Seven
deliberate mutations, each asserted to be caught, plus a direct
roll-up unit test (`python mutation_check.py`):

| mutation | what it breaks | caught by | survivors |
|---|---|---|---|
| M1 undetermined-as-compliant | silence reads as compliance | 15 vectors | 22/37 |
| M2 missing-fields-pass | absent fields return a clean pass | 17 vectors | 20/37 |
| M3 attribute-policy hard-coded | D7 doctrine baked into code | V-J2 | 36/37 |
| M4 severity-inflation | moderate failure escalated to grave | V-F4, V-J7, V-C2 | 34/37 |
| M5 determinative-over-fires | any score mention counts as determinative | 26 vectors | 11/37 |
| M6 warning-list hard-coded | D1 doctrine baked into code | V-J4 | 36/37 |
| M7 decision-points hard-coded | D5 doctrine baked into code | V-J6 | 36/37 |

**7/7 caught; roll-up unit test 8/8; restored logic reproduces 37/37
exactly.**

## The iteration this went through (worth reporting in the paper)

The first pass ran **31/31 clean on the first try** — and the mutation
gate is what turned that into information:

1. **M3 was caught by exactly one vector** (the D7 profile swap). The
   swap pair was the *entire* defence against the specific failure the
   "no ad-hoc logic" claim is about, and it existed for only one of
   the four profile-parameterized gates.
2. So swap pairs were added for D1, D4, and D5 (V-J3…V-J8, 31 → 37
   vectors), and two new hard-coding mutants written to test them.
3. **M6 and M7 are each caught by exactly one vector, and that vector
   is new** (V-J4, V-J6). It follows directly that before this
   iteration, doctrine hard-coded into D1 or D5 would have survived
   the entire suite undetected.

Each parameterized gate now has a margin of exactly one — its own swap
pair — which is by design rather than by accident: the swap pair *is*
the instrument for that gate's hard-coding failure. The residual risk
is that a swap pair could be dropped or mis-specified, so the pairs
are marked in `vectors.py` as load-bearing.

**M4's margin is structural, not fixable by vectors:** D4 is the only
`moderate`-severity gate, so severity roll-up was exercised through
one gate. Rather than inventing a second moderate gate to make the
metric look better, the roll-up rule is now tested directly on
synthetic finding sets (8 cases, including "undetermined alone blocks
`permissible`" and "minor failure does not escalate").

## Reproduce

```
PYTHONPATH=<path-to>/erisml-compiler/src python run_vectors.py
PYTHONPATH=<path-to>/erisml-compiler/src python mutation_check.py
```

Artifacts: `vector_results.json`, `mutation_results.json`.

## Still open before any seal

1. ⧗ doctrine quote-verification against 881 N.W.2d 749 (pin cites).
2. Legal review of the encodings.
3. ~~vector-coverage actions~~ — done this pass (swap pairs for every
   parameterized gate; roll-up unit test replacing the structural M4
   gap).
4. E4 (auditability gap) is *predicted* at 4/7 but not yet measured;
   measuring it needs the COMPAS records mapped into `DecisionRecord`,
   which is the next code step.
5. P2's calibration draws (the RQ2 pipeline) are untouched — that is
   the next subsystem, and it is independent of the doctrine
   verification blocking items 1–2.
