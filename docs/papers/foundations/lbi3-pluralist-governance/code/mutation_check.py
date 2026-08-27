"""Does the vector set have teeth? (instrument gate for RQ1/E1)

A suite written by the same hand as the code it tests will pass on the
first run; that is evidence of nothing. This applies deliberate
mutations to the gate logic and asserts each one is CAUGHT. A mutation
that survives marks a hole in the vector set, and the vector set is
what E1 rests on.

Discipline inherited from the OT campaigns: interpret the instrument
before the result.

Run:  python mutation_check.py
Exit code 0 iff every mutation is caught.
"""

from __future__ import annotations

import json
import sys

import doctrinal
from doctrinal import DecisionRecord, DoctrinalProjection, GateFinding
from run_vectors import check_vectors

MUTATIONS: list[tuple[str, str]] = []


def mutation(name: str, description: str):
    def deco(fn):
        MUTATIONS.append((name, description))
        fn._mut_name = name
        return fn
    return deco


# --- M1: silence reads as compliance (THE deployment failure mode) -------
@mutation("M1_undetermined_as_compliant",
          "undetermined gates no longer block a `permissible` verdict")
def mut_undetermined_as_compliant():
    orig = DoctrinalProjection.project

    def patched(self, substrate=None, *, graph=None, record=None, profile=None, **kw):
        res = orig(self, substrate, graph=graph, record=record, profile=profile, **kw)
        if res.verdict == "requires_review" and res.framework_specific["n_fired"] == 0:
            return res.model_copy(update={"verdict": "permissible", "polarity": "permit"})
        return res

    DoctrinalProjection.project = patched
    return lambda: setattr(DoctrinalProjection, "project", orig)


# --- M2: missing fields silently pass instead of undetermined -----------
@mutation("M2_missing_fields_pass",
          "a gate with absent required fields returns a clean pass")
def mut_missing_fields_pass():
    orig = doctrinal._undetermined

    def patched(name, missing, severity):
        return GateFinding(name=name, passed=True, reason="ok", severity=severity)

    doctrinal._undetermined = patched
    return lambda: setattr(doctrinal, "_undetermined", orig)


# --- M3: attribute policy ignores the profile (doctrine hard-coded) ------
@mutation("M3_attribute_policy_ignores_profile",
          "D7 hard-codes race as foreclosed instead of reading the profile")
def mut_attribute_hardcoded():
    orig = DoctrinalProjection._d7_attribute_policy

    def patched(self, r, p):
        if r.instrument_inputs is None:
            return doctrinal._undetermined("attribute_policy", ["instrument_inputs"],
                                           "catastrophic")
        bad = [a for a in r.instrument_inputs if a == "race"]
        return GateFinding(
            name="attribute_policy", passed=not bad,
            reason="hard-coded race check", severity="catastrophic", subjects=bad,
        )

    DoctrinalProjection._d7_attribute_policy = patched
    return lambda: setattr(DoctrinalProjection, "_d7_attribute_policy", orig)


# --- M4: severity inflation (moderate treated as grave) -----------------
@mutation("M4_severity_inflation",
          "D4 population-validation failure escalated from moderate to grave")
def mut_severity_inflation():
    orig = DoctrinalProjection._d4_validated_for_population

    def patched(self, r, p):
        f = orig(self, r, p)
        if not f.passed:
            return f.model_copy(update={"severity": "grave"})
        return f

    DoctrinalProjection._d4_validated_for_population = patched
    return lambda: setattr(DoctrinalProjection, "_d4_validated_for_population", orig)


# --- M5: over-firing (any score mention counts as determinative) --------
@mutation("M5_determinative_overfires",
          "D2 fires whenever the score appears in the stated basis at all")
def mut_determinative_overfires():
    orig = DoctrinalProjection._d2_not_determinative

    def patched(self, r, p):
        if r.stated_basis is None:
            return doctrinal._undetermined("not_determinative", ["stated_basis"],
                                           "catastrophic")
        fired = "risk_score" in r.stated_basis
        return GateFinding(
            name="not_determinative", passed=not fired,
            reason="over-firing mutant", severity="catastrophic",
        )

    DoctrinalProjection._d2_not_determinative = patched
    return lambda: setattr(DoctrinalProjection, "_d2_not_determinative", orig)


MUTATORS = [
    mut_undetermined_as_compliant, mut_missing_fields_pass,
    mut_attribute_hardcoded, mut_severity_inflation,
    mut_determinative_overfires,
]


def main() -> int:
    baseline_pass, _ = check_vectors()
    total = baseline_pass  # baseline must be 31/31 before mutating
    print(f"baseline: {baseline_pass} vectors pass")
    if baseline_pass != 31:
        print("baseline is not clean; fix before mutation testing")
        return 1

    results = []
    for mutator, (name, desc) in zip(MUTATORS, MUTATIONS):
        undo = mutator()
        try:
            n_pass, failures = check_vectors()
        finally:
            undo()
        caught = n_pass < total
        results.append({
            "mutation": name, "description": desc, "caught": caught,
            "vectors_still_passing": n_pass,
            "caught_by": [f["vector"] for f in failures][:6],
        })
        status = "CAUGHT" if caught else "SURVIVED"
        print(f"  {status:8s} {name}: {n_pass}/{total} still pass"
              f"{' — by ' + ', '.join(r for r in results[-1]['caught_by']) if caught else ''}")

    # restored logic must reproduce the baseline exactly
    restored, _ = check_vectors()
    ok = all(r["caught"] for r in results) and restored == total
    print(f"\nrestored baseline: {restored}/{total}")
    print(f"MUTATION GATE: {'PASS' if ok else 'FAIL'} "
          f"({sum(r['caught'] for r in results)}/{len(results)} mutations caught)")

    with open("mutation_results.json", "w") as fh:
        json.dump({"baseline": baseline_pass, "restored": restored,
                   "results": results, "gate_met": ok}, fh, indent=1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
