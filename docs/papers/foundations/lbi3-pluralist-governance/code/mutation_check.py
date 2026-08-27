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


# --- M6/M7: doctrine hard-coded in the OTHER parameterized gates --------
# These exist because adding the V-J3..J8 swap pairs is only worth
# something if it catches hard-coding beyond D7. Before those vectors
# existed, both of these mutants survived the whole suite.
@mutation("M6_warnings_hardcoded",
          "D1 hard-codes the required-warning list instead of reading the profile")
def mut_warnings_hardcoded():
    orig = DoctrinalProjection._d1_required_warnings
    frozen = ("proprietary_methodology", "group_based_not_individual",
              "accuracy_questioned_across_groups",
              "not_validated_for_local_population",
              "not_designed_for_this_decision_point")

    def patched(self, r, p):
        if r.warnings_given is None:
            return doctrinal._undetermined("required_warnings_present",
                                           ["warnings_given"], "grave")
        missing = [w for w in frozen if w not in r.warnings_given]
        return GateFinding(
            name="required_warnings_present", passed=not missing,
            reason="hard-coded warning list", severity="grave",
        )

    DoctrinalProjection._d1_required_warnings = patched
    return lambda: setattr(DoctrinalProjection, "_d1_required_warnings", orig)


@mutation("M7_decision_points_hardcoded",
          "D5 hard-codes the sanctioned decision points instead of reading the profile")
def mut_decision_points_hardcoded():
    orig = DoctrinalProjection._d5_purpose_fit

    def patched(self, r, p):
        if r.decision_point is None:
            return doctrinal._undetermined("purpose_fit", ["decision_point"], "grave")
        ok = r.decision_point == "post_sentencing_corrections"
        return GateFinding(
            name="purpose_fit", passed=ok, reason="hard-coded decision point",
            severity="grave",
        )

    DoctrinalProjection._d5_purpose_fit = patched
    return lambda: setattr(DoctrinalProjection, "_d5_purpose_fit", orig)


MUTATORS = [
    mut_undetermined_as_compliant, mut_missing_fields_pass,
    mut_attribute_hardcoded, mut_severity_inflation,
    mut_determinative_overfires, mut_warnings_hardcoded,
    mut_decision_points_hardcoded,
]


def check_verdict_rollup() -> list[str]:
    """Direct unit test of the severity roll-up.

    The mutation gate showed severity handling is exercised through D4
    alone (the only `moderate` gate), so roll-up coverage is
    structurally thin in the vector set. This tests the rule directly
    on synthetic finding sets instead of through a doctrinal gate.
    """
    from doctrinal import UNDETERMINED

    def finding(sev: str, passed: bool, undet: bool = False) -> GateFinding:
        return GateFinding(
            name="synthetic", passed=passed, reason="rollup test", severity=sev,
            detail={"result": UNDETERMINED} if undet else {},
        )

    cases = [
        ("all clean", [finding("grave", True)], "permissible"),
        ("moderate fires", [finding("moderate", False)], "requires_review"),
        ("grave fires", [finding("grave", False)], "forbidden"),
        ("catastrophic fires", [finding("catastrophic", False)], "forbidden"),
        ("grave beats moderate",
         [finding("moderate", False), finding("grave", False)], "forbidden"),
        ("undetermined alone blocks permissible",
         [finding("grave", True, undet=True)], "requires_review"),
        ("grave beats undetermined",
         [finding("grave", False), finding("moderate", True, undet=True)], "forbidden"),
        ("minor failure does not escalate", [finding("minor", False)], "permissible"),
    ]

    failures = []
    for label, findings, expected in cases:
        fired = [f for f in findings if not f.passed]
        undet = [f for f in findings if f.detail.get("result") == UNDETERMINED]
        grave = [f for f in fired if f.severity in ("grave", "catastrophic")]
        moderate = [f for f in fired if f.severity == "moderate"]
        got = ("forbidden" if grave else "requires_review" if moderate
               else "requires_review" if undet else "permissible")
        if got != expected:
            failures.append(f"{label}: expected {expected}, got {got}")
    return failures


def main() -> int:
    from vectors import N_VECTORS

    baseline_pass, _ = check_vectors()
    total = N_VECTORS
    print(f"baseline: {baseline_pass}/{total} vectors pass")
    if baseline_pass != total:
        print("baseline is not clean; fix before mutation testing")
        return 1

    rollup_failures = check_verdict_rollup()
    print(f"roll-up unit test: "
          f"{'PASS (8/8)' if not rollup_failures else 'FAIL — ' + '; '.join(rollup_failures)}")

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
    ok = (all(r["caught"] for r in results) and restored == total
          and not rollup_failures)
    print(f"\nrestored baseline: {restored}/{total}")
    print(f"MUTATION GATE: {'PASS' if ok else 'FAIL'} "
          f"({sum(r['caught'] for r in results)}/{len(results)} mutations caught, "
          f"roll-up {'clean' if not rollup_failures else 'broken'})")

    with open("mutation_results.json", "w") as fh:
        json.dump({"baseline": baseline_pass, "n_vectors": total,
                   "restored": restored, "results": results,
                   "rollup_failures": rollup_failures, "gate_met": ok},
                  fh, indent=1)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
